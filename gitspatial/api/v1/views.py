import json

from django.conf import settings
from django.http import Http404, HttpResponse, HttpResponseBadRequest

from gitspatial.models import Repo, FeatureSet, Feature
from ..decorators import jsonp
from ..exceptions import InvalidSpatialParameterException
from ..helpers import query_args


default_limit = 50


@jsonp
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


def bad_request(message):
    response = {'status': 'error', 'message': message}
    indent = 2 if settings.DEBUG else None
    content = json.dumps(response, indent=indent)
    return HttpResponseBadRequest(content, content_type='application/json')
