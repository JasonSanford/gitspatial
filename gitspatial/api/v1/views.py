from django.http import Http404
from django.shortcuts import HttpResponse
from django.contrib.gis.geos.polygon import Polygon

from gitspatial.models import Repo, FeatureSet, Feature


def feature_set_query(request, user_name, repo_name, feature_set_name):
    full_name = '{0}/{1}'.format(user_name, repo_name)
    try:
        repo = Repo.objects.get(full_name=full_name)
        feature_set = FeatureSet.objects.get(repo=repo, name=feature_set_name)
    except (Repo.DoesNotExist, FeatureSet.DoesNotExist):
        raise Http404

    filter_kwargs = {
        'feature_set': feature_set,
    }
    spatial_args = None

    if 'bbox' in request.GET:
        spatial_args = _by_bbox(request.GET['bbox'])

    if spatial_args is not None:
        filter_kwargs.update(spatial_args)

    features = Feature.objects.filter(**filter_kwargs)

    return HttpResponse('Feature count is is {0}.'.format(len(features)))


def _by_bbox(bbox_string):
    bbox = bbox_string.split(',')
    bbox = map(float, bbox)

    return {
        'geom__intersects': Polygon.from_bbox(bbox)
    }
