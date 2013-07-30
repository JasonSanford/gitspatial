import json
import logging

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.shortcuts import render, HttpResponse
from django.views.decorators.http import require_http_methods

from ..github import GitHubApiPostRequest, GitHubApiGetRequest, GitHubApiDeleteRequest
from ..models import Repo
from ..tasks import get_user_repos, get_repo_feature_sets


logger = logging.getLogger(__name__)


@login_required
def user_landing(request):
    """
    GET /user/

    User landing page
    """
    # TODO: Only do this at sign up. Subsequent re-checks of new/updated repos should be scheduled.
    get_user_repos.apply_async((request.user,))
    return render(request, 'user.html')


@login_required
@require_http_methods(['POST', 'DELETE'])
def repo_sync(request, repo_id):
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
        hook_request = GitHubApiPostRequest(request.user, '/repos/{0}/hooks'.format(repo.full_name), hook_data)
        if hook_request.status_code == 204:
            logger.info('Hook created for repo: {0}'.format(repo))
        else:
            logger.info('Hook not created for repo: {0}'.format(repo))
        repo.save()
        get_repo_feature_sets.apply_async((repo,))
        return HttpResponse(json.dumps({'status': 'ok'}), content_type='application/json', status=201)
    else:  # DELETE
        repo.synced = False
        hook_request = GitHubApiGetRequest(request.user, '/repos/{0}/hooks'.format(repo.full_name))
        hook_id_to_delete = None

        for hook in hook_request.json:
            if 'url' in hook['config'] and hook['config']['url'] == repo.hook_url:
                hook_id_to_delete = hook['id']
                continue

        if hook_id_to_delete is not None:
            hook_delete_request = GitHubApiDeleteRequest(request.user, '/repos/{0}/hooks/{1}'.format(repo.full_name, hook_id_to_delete))
            if hook_delete_request.status_code != 204:
                logger.warning('Hook not deleted for repo: {0}'.format(repo))
            else:
                logger.warning('Hook deleted for repo: {0}'.format(repo))
        repo.save()
        return HttpResponse(json.dumps({'status': 'ok'}), content_type='application/json', status=204)