import json

import validictory

import schemas as geojson_schemas


geojson_types = {
    'Point': geojson_schemas.point,
    'MultiPoint': geojson_schemas.multipoint,
    'LineString': geojson_schemas.linestring,
    'MultiLineString': geojson_schemas.multilinestring,
    'Polygon': geojson_schemas.polygon,
    'MultiPolygon': geojson_schemas.multipolygon,
    'GeometryCollection': geojson_schemas.geometrycollection,
}


class GeoJSONParserException(Exception):
    pass


class GeoJSONParser:
    def __init__(self, geojson_string):
        filtered_geojson = {'type': 'FeatureCollection', 'features': []}
        try:
            test_geojson = json.loads(geojson_string)
            if not isinstance(test_geojson, dict):
                raise GeoJSONParserException('Content was not a JSON object.')
        except (ValueError, TypeError):
            raise GeoJSONParserException('Content was not JSON serializeable.')

        if not 'type' in test_geojson:
            raise GeoJSONParserException('The "type" member is requried and was not found.')

        if test_geojson['type'] != 'FeatureCollection':
            raise GeoJSONParserException('GeoJSON object must be of type FeatureCollection. The passed type was {0}.'.format(test_geojson['type']))
        elif not ('features' in test_geojson and isinstance(test_geojson['features'], (list, tuple))):
            raise GeoJSONParserException('GeoJSON object must have member named "features" as an array of Features.')

        for feature in test_geojson['features']:
            if not ('type' in feature and feature['type'] == 'Feature' and 'properties' in feature and 'geometry' in feature):
                raise GeoJSONParserException('GeoJSON Features must have a type of "Feature" and "properties" and "geometry" members.')
            if feature['geometry'] is None:
                # null geometries are valid. Move along.
                continue
            if feature['geometry']['type'] not in geojson_types:
                raise GeoJSONParserException('{0} is not a valid GeoJSON geometry.'.format(feature['geometry']['type']))
            try:
                validictory.validate(feature['geometry'], geojson_types[feature['geometry']['type']])
            except validictory.validator.ValidationError as e:
                raise GeoJSONParserException('GeoJSON validation error. Message: {0}.'.format(e.message))
            filtered_geojson['features'].append(feature)

        # Everything's good
        self.features = filtered_geojson['features']
