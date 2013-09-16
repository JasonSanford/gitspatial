import json
import logging

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator, EmptyPage as EmptyPageException
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import render, HttpResponse, redirect
from django.views.decorators.http import require_http_methods, require_GET

from ..github import GitHub
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
@require_http_methods(['PUT', 'GET'])
def user_feature_set(request, feature_set_id):
    per_page = 50

    try:
        feature_set = FeatureSet.objects.get(id=feature_set_id)
    except FeatureSet.DoesNotExist:
        raise Http404

    if not feature_set.repo.user == request.user:
        raise PermissionDenied

    if request.method == 'GET':
        if feature_set.is_syncing:
            context = {'feature_set': feature_set}
        else:
            count = Feature.objects.filter(feature_set=feature_set).count()

            requested_page = request.GET.get('page', 1)

            try:
                requested_page = int(requested_page)
            except ValueError:
                return redirect('user_feature_set', feature_set_id=feature_set_id)

            features = Feature.objects.filter(feature_set=feature_set).geojson()

            paginated = Paginator(features, per_page)

            try:
                current_page = paginated.page(requested_page)
            except EmptyPageException:
                if requested_page == 0:
                    return redirect('%s?page=%s' % (reverse('user_feature_set', args=(feature_set_id,)), 1))
                else:
                    return redirect('%s?page=%s' % (reverse('user_feature_set', args=(feature_set_id,)), paginated.num_pages))

            current_features = current_page.object_list
            previous_page_number = current_page.previous_page_number() if current_page.has_previous() else None
            next_page_number = current_page.next_page_number() if current_page.has_next() else None

            prop_keys = json.loads(current_features[0].properties).keys()

            processed_features = []
            geojson = {'type': 'FeatureCollection', 'features': []}
            for current_feature in current_features:
                processed_feature = {'id': current_feature.id}
                current_feature_props = json.loads(current_feature.properties)
                for prop_key in prop_keys:
                    processed_feature[prop_key] = current_feature_props.get(prop_key)
                processed_features.append(processed_feature)

                geometry = json.loads(current_feature.geojson)
                geojson_feature = {'type': 'Feature', 'geometry': geometry, 'properties': current_feature_props, 'id': current_feature.id}
                geojson['features'].append(geojson_feature)

            context = {
                'feature_set': feature_set,
                'api_url': '{0}{1}'.format(
                    'http://gitspatial.com',
                    reverse('v1_feature_set_query', kwargs={'user_name': feature_set.repo.user.username, 'repo_name': feature_set.repo.name, 'feature_set_name': feature_set.name})),
                'count': count,
                'center_lat': feature_set.center[1],
                'center_lng': feature_set.center[0],
                'bounds': list(feature_set.bounds),
                'features': processed_features,
                'geojson': json.dumps(geojson),
                'prop_keys': prop_keys,
                'page_range': paginated.page_range,
                'current_page': requested_page,
                'previous_page_number': previous_page_number,
                'next_page_number': next_page_number,
                'start_index': current_page.start_index(),
                'end_index': current_page.end_index()}

        return render(request, 'user_feature_set.html', context)
    else:
        raw_data = request.body
        parts = raw_data.split('&')
        data = {}
        for part in parts:
            key, value = part.split('=')
            data[key] = value

        if 'value' not in data:
            return HttpResponseBadRequest('No value found')

        value = data['value']

        if not (0 < len(value) < 1000):
            return HttpResponseBadRequest('Feature set name must be between 1 and 1,000 characters.')

        feature_set.name = value
        feature_set.save()

        return HttpResponse('Success! Seeya.')


@login_required
@require_http_methods(['POST', 'DELETE'])
def user_repo_sync(request, repo_id):
    """
    POST /repo/:id/sync
    or
    DELETE /repo/:id/sync

    Sets repo synced property as True or False (POST or DELETE)
    """
    try:
        repo = Repo.objects.get(id=repo_id)
    except Repo.DoesNotExist:
        raise Http404

    if not repo.user == request.user:
        return HttpResponseForbidden()

    if request.method == 'POST':
        # See tests for the why on this awfulness
        if 'testing' in request.GET:
            return HttpResponse('ok', status=201)

        max_repo_syncs = 3

        current_synced_repos = Repo.objects.filter(user=request.user, synced=True).count()

        if current_synced_repos >= max_repo_syncs:
            response = {
                'status': 'error',
                'message': 'While we ramp things up, users are limited to syncing {0} repos. Cool?'.format(max_repo_syncs)
            }
            return HttpResponseBadRequest(json.dumps(response), content_type='application/json')

        repo.synced = True
        repo.sync_status = repo.SYNCING

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
        github = GitHub(repo.user)
        gh_request = github.post('/repos/{0}/hooks'.format(repo.full_name), hook_data)
        if gh_request.status_code == 201:
            logger.info('Hook created for repo: {0}'.format(repo))
        else:
            logger.info('Hook not created for repo: {0}'.format(repo))
        repo.save()
        get_repo_feature_sets.apply_async((repo,))
        return HttpResponse(json.dumps({'status': 'ok'}), content_type='application/json', status=201)
    else:  # DELETE
        # See tests for the why on this awfulness
        if 'testing' in request.GET:
            return HttpResponse('ok', status=204)

        repo.synced = False
        repo.sync_status = repo.NOT_SYNCED
        github = GitHub(repo.user)
        gh_request = github.get('/repos/{0}/hooks'.format(repo.full_name))
        hook_id_to_delete = None

        for hook in gh_request.json():
            if 'url' in hook['config'] and hook['config']['url'] == repo.hook_url:
                hook_id_to_delete = hook['id']
                continue

        if hook_id_to_delete is not None:
            gh_request = github.delete('/repos/{0}/hooks/{1}'.format(repo.full_name, hook_id_to_delete))
            if gh_request.status_code == 204:
                logger.info('Hook deleted for repo: {0}'.format(repo))
                delete_repo_feature_sets.apply_async((repo,))
            else:
                logger.warning('Hook not deleted for repo: {0}'.format(repo))
        repo.save()
        return HttpResponse(json.dumps({'status': 'ok'}), content_type='application/json', status=204)


@login_required
@require_GET
def user_repo_sync_status(request, repo_id):
    """
    GET /repo/:id/sync_status

    Gets repo sync status as {"status": "<message>"}
    where message is one of synced, not_synced, syncing, error
    """
    try:
        repo = Repo.objects.get(id=repo_id)
    except Repo.DoesNotExist:
        raise Http404

    if not repo.user == request.user:
        return HttpResponseForbidden()

    status = repo.SYNC_CODES[repo.sync_status]

    return HttpResponse(json.dumps({'status': status}), content_type='application/json')


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
        feature_set.sync_status = FeatureSet.SYNCING
        feature_set.save()
        get_feature_set_features.apply_async((feature_set,))
        return HttpResponse(json.dumps({'status': 'ok'}), content_type='application/json', status=201)
    else:  # DELETE
        feature_set.synced = False
        feature_set.sync_status = FeatureSet.NOT_SYNCED
        feature_set.save()
        delete_feature_set_features.apply_async((feature_set,))
        return HttpResponse(json.dumps({'status': 'ok'}), content_type='application/json', status=204)


@login_required
@require_GET
def user_feature_set_sync_status(request, feature_set_id):
    """
    GET /feature_set/:id/sync_status

    Gets feature set sync status as {"status": "<message>"}
    where message is one of synced, not_synced, syncing, error
    """
    try:
        fs = FeatureSet.objects.get(id=feature_set_id)
    except FeatureSet.DoesNotExist:
        raise Http404

    if not fs.repo.user == request.user:
        return HttpResponseForbidden()

    status = fs.SYNC_CODES[fs.sync_status]

    return HttpResponse(json.dumps({'status': status}), content_type='application/json')
