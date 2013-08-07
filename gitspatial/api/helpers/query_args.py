from django.contrib.gis.geos.polygon import Polygon

from ..exceptions import InvalidSpatialParameterException


def by_bbox(bbox_string):
    bbox = bbox_string.split(',')

    if len(bbox) != 4:
        raise InvalidSpatialParameterException('The bbox parameter must contain 4 items: xmin, ymin, xmax, ymax')

    try:
        bbox = map(float, bbox)
    except ValueError:
        raise InvalidSpatialParameterException('Items in the bbox parameter must be parseable as floats')

    return {
        'geom__intersects': Polygon.from_bbox(bbox)
    }
