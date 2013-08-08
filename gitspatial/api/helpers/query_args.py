from django.contrib.gis.geos.polygon import Polygon
from django.contrib.gis.geos.point import Point
from django.contrib.gis.measure import D

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


def by_lat_lon_distance(lat, lon, distance):
    try:
        lat = float(lat)
        lon = float(lon)
        distance = float(distance)
    except ValueError:
        raise InvalidSpatialParameterException('Parameters lat, lon and distance must be parseable as floats')

    point = Point(x=lon, y=lat, srid=4326)

    return {
        'geom__distance_lte': (point, D(m=distance))
    }
