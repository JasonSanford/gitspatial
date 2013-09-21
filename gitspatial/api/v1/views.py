import json
import logging

from django.conf import settings
from django.http import Http404, HttpResponse, HttpResponseBadRequest
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from gitspatial.models import Repo, FeatureSet, Feature
from ..decorators import jsonp
from ..exceptions import InvalidSpatialParameterException
from ..helpers import query_args
from ...tasks import get_feature_set_features, get_repo_feature_sets


default_limit = 1000

logger = logging.getLogger(__name__)


def docs(request):
    return render(request, 'api_v1.html')


@jsonp
@require_GET
def feature_set_query(request, user_name, repo_name, feature_set_name):
    full_name = '{0}/{1}'.format(user_name, repo_name)
    try:
        repo = Repo.objects.get(full_name=full_name)
        feature_set = FeatureSet.objects.get(repo=repo, name=feature_set_name)
    except (Repo.DoesNotExist, FeatureSet.DoesNotExist):
        raise Http404

    if not feature_set.synced:
        raise Http404

    limit = request.GET.get('limit', default_limit)
    offset = request.GET.get('offset', 0)

    try:
        limit = int(limit)
    except ValueError:
        limit = default_limit
    if limit > default_limit:
        limit = default_limit

    try:
        offset = int(offset)
    except ValueError:
        offset = 0

    filter_kwargs = {
        'feature_set': feature_set,
    }
    spatial_args = None

    if 'bbox' in request.GET:
        try:
            spatial_args = query_args.by_bbox(request.GET['bbox'])
        except InvalidSpatialParameterException as ex:
            return bad_request(str(ex))
    elif 'lat' in request.GET and 'lon' in request.GET and 'distance' in request.GET:
        try:
            spatial_args = query_args.by_lat_lon_distance(request.GET['lat'], request.GET['lon'], request.GET['distance'])
        except InvalidSpatialParameterException as ex:
            return bad_request(str(ex))

    if spatial_args is not None:
        filter_kwargs.update(spatial_args)

    total_count = Feature.objects.filter(**filter_kwargs).count()

    features = Feature.objects.filter(**filter_kwargs).geojson()[offset:offset+limit]
    json_features = [
        {
            'type': 'Feature',
            'properties': json.loads(feature.properties),
            'geometry': json.loads(feature.geojson),
            'id': feature.id,
        } for feature in features
    ]
    response = {'type': 'FeatureCollection', 'features': json_features, 'count': len(features), 'total_count': total_count}
    indent = 2 if settings.DEBUG else None
    content = json.dumps(response, indent=indent)

    return HttpResponse(content, content_type='application/json')


@require_POST
@csrf_exempt
def repo_hook(request, repo_id):
    payload = json.loads(request.body)
    repo = Repo.objects.get(github_id=payload['repository']['id'])

    modified, removed, added = [], [], []
    for commit in payload['commits']:
        for path in commit['modified']:
            if path not in modified:
                modified.append(path)
        for path in commit['removed']:
            if path not in removed:
                removed.append(path)
        for path in commit['added']:
            if path not in added:
                added.append(path)

    for path in modified:
        feature_set = FeatureSet.objects.get(repo=repo, path=path)
        logger.info('[github_hook]: Getting features for {0}'.format(feature_set))
        get_feature_set_features.apply_async((feature_set,))

    for path in removed:
        feature_sets = FeatureSet.objects.filter(repo=repo, path=path)
        for feature_set in feature_sets:
            logger.info('[github_hook]: Deleting feature set for {0}'.format(feature_set))
            feature_set.delete()

    if added:
        get_repo_feature_sets.apply_async((repo,))

    return HttpResponse('Thanks GitHub!')


def bad_request(message):
    response = {'status': 'error', 'message': message}
    indent = 2 if settings.DEBUG else None
    content = json.dumps(response, indent=indent)
    return HttpResponseBadRequest(content, content_type='application/json')
