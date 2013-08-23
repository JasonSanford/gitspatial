import json
import logging

from django.conf import settings
from django.http import Http404, HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from gitspatial.models import Repo, FeatureSet, Feature
from ..decorators import jsonp
from ..exceptions import InvalidSpatialParameterException
from ..helpers import query_args


default_limit = 50

logger = logging.getLogger(__name__)


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

    features = Feature.objects.filter(**filter_kwargs).geojson()[offset:offset+limit]
    json_features = [
        {
            'type': 'Feature',
            'properties': json.loads(feature.properties),
            'geometry': json.loads(feature.geojson)
        } for feature in features
    ]
    response = {'type': 'FeatureCollection', 'features': json_features}
    indent = 2 if settings.DEBUG else None
    content = json.dumps(response, indent=indent)

    return HttpResponse(content, content_type='application/json')


@require_POST
@csrf_exempt
def repo_hook(request, repo_id):
    logger.info('request.body is')
    logger.info(request.body)
    logger.info('post is')
    logger.info(request.POST)
    logger.info('content-type is')
    logger.info(request.META['CONTENT_TYPE'])
    raw_payload = request.POST['payload']
    payload = json.loads(raw_payload)
    logger.info('got post-receive hook from github')
    logger.info(payload)
    return HttpResponse('Thanks GitHub!')


def bad_request(message):
    response = {'status': 'error', 'message': message}
    indent = 2 if settings.DEBUG else None
    content = json.dumps(response, indent=indent)
    return HttpResponseBadRequest(content, content_type='application/json')
