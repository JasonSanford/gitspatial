import json
import logging

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponseBadRequest
from django.shortcuts import render, HttpResponse
from django.views.decorators.http import require_http_methods

from ..github import GitHubApiPostRequest, GitHubApiGetRequest, GitHubApiDeleteRequest
from ..models import Repo, FeatureSet, Feature
from ..tasks import get_user_repos, get_repo_feature_sets, delete_repo_feature_sets, get_feature_set_features, delete_feature_set_features


logger = logging.getLogger(__name__)


@login_required
def user_landing(request):
    """
    GET /user/

    User landing page
    """
    # TODO: Only do this at sign up. Subsequent re-checks of new/updated repos should be scheduled.
    get_user_repos.apply_async((request.user,))
    user_repos = Repo.objects.filter(user=request.user).extra(select={'lower_name': 'lower(name)'}).order_by('lower_name')
    context = {'user_repos': user_repos}
    return render(request, 'user.html', context)


@login_required
def user_repo(request, repo_id):
    try:
        repo = Repo.objects.get(id=repo_id)
    except Repo.DoesNotExist:
        raise Http404
    feature_sets = FeatureSet.objects.filter(repo=repo).order_by('name')
    context = {'repo': repo, 'feature_sets': feature_sets}
    return render(request, 'user_repo.html', context)


@login_required
def user_feature_set(request, feature_set_id):
    try:
        feature_set = FeatureSet.objects.get(id=feature_set_id)
    except FeatureSet.DoesNotExist:
        raise Http404
    count = Feature.objects.filter(feature_set=feature_set).count()
    context = {'feature_set': feature_set, 'count': count}
    return render(request, 'user_feature_set.html', context)


@login_required
@require_http_methods(['POST', 'DELETE'])
def user_repo_sync(request, repo_id):
    """
    POST /repo/:id
    or
    DELETE /repo/:id

    Sets repo synced property as True or False (POST or DELETE)
    """
    try:
        repo = Repo.objects.get(id=repo_id)
    except Repo.DoesNotExist:
        raise Http404

    if not repo.user == request.user:
        raise PermissionDenied

    if request.method == 'POST':
        max_repo_syncs = 3

        current_synced_repos = Repo.objects.filter(user=request.user, synced=True).count()

        if current_synced_repos >= max_repo_syncs:
            response = {
                'status': 'error',
                'message': 'While we ramp things up, users are limited to syncing {0} repos. Cool?'.format(max_repo_syncs)
            }
            return HttpResponseBadRequest(json.dumps(response), content_type='application/json')

        repo.synced = True

        # Create a GitHub web hook so we get notified when this repo is pushed
        hook_data = {
            'name': 'web',
            'active': True,
            'events': ['push'],
            'config': {
                'url': repo.hook_url,
                'content_type': 'json'
            }
        }
        gh_request = GitHubApiPostRequest(request.user, '/repos/{0}/hooks'.format(repo.full_name), hook_data)
        if gh_request.response.status_code == 204:
            logger.info('Hook created for repo: {0}'.format(repo))
        else:
            logger.info('Hook not created for repo: {0}'.format(repo))
        repo.save()
        get_repo_feature_sets.apply_async((repo,))
        return HttpResponse(json.dumps({'status': 'ok'}), content_type='application/json', status=201)
    else:  # DELETE
        repo.synced = False
        gh_request = GitHubApiGetRequest(request.user, '/repos/{0}/hooks'.format(repo.full_name))
        hook_id_to_delete = None

        for hook in gh_request.response.json():
            if 'url' in hook['config'] and hook['config']['url'] == repo.hook_url:
                hook_id_to_delete = hook['id']
                continue

        if hook_id_to_delete is not None:
            gh_request = GitHubApiDeleteRequest(request.user, '/repos/{0}/hooks/{1}'.format(repo.full_name, hook_id_to_delete))
            if gh_request.response.status_code == 204:
                logger.info('Hook deleted for repo: {0}'.format(repo))
                delete_repo_feature_sets.apply_async((repo,))
            else:
                logger.warning('Hook not deleted for repo: {0}'.format(repo))
        repo.save()
        return HttpResponse(json.dumps({'status': 'ok'}), content_type='application/json', status=204)


@login_required
@require_http_methods(['POST', 'DELETE'])
def user_feature_set_sync(request, feature_set_id):
    """
    POST /feature_set/:id
    or
    DELETE /feature_set/:id

    Sets feature set synced property as True or False (POST or DELETE)
    """
    try:
        feature_set = FeatureSet.objects.get(id=feature_set_id)
    except FeatureSet.DoesNotExist:
        raise Http404

    if not feature_set.repo.user == request.user:
        raise PermissionDenied

    if request.method == 'POST':
        feature_set.synced = True
        feature_set.save()
        get_feature_set_features.apply_async((feature_set,))
        return HttpResponse(json.dumps({'status': 'ok'}), content_type='application/json', status=201)
    else:  # DELETE
        feature_set.synced = False
        feature_set.save()
        delete_feature_set_features.apply_async((feature_set,))
        return HttpResponse(json.dumps({'status': 'ok'}), content_type='application/json', status=204)
