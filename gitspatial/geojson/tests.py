import logging

from django.test import TestCase

from . import GeoJSONParser, test_features, GeoJSONParserException

logger = logging.getLogger(__name__)
logger.setLevel(logging.CRITICAL)


class GeoJSONTest(TestCase):
    def setUp(self):
        pass

    def test_good_features(self):
        geojson = GeoJSONParser(test_features.featurecollection)
        self.assertEqual(len(geojson.features), 7)

    def test_none_geometries(self):
        geojson = GeoJSONParser(test_features.featurecollection_with_nones)
        self.assertEqual(len(geojson.features), 5)

    def test_not_an_object(self):
        try:
            geojson = GeoJSONParser(test_features.feature_collection_not_an_object)
        except Exception as e:
            pass
        self.assertTrue(isinstance(e, GeoJSONParserException))
        self.assertEqual(str(e), 'Content was not a JSON object.')

    def test_not_serializeable(self):
        try:
            geojson = GeoJSONParser(test_features.featurecollection_not_serializeable)
        except Exception as e:
            pass
        self.assertTrue(isinstance(e, GeoJSONParserException))
        self.assertEqual(str(e), 'Content was not JSON serializeable.')

    def test_not_a_featurecollection(self):
        try:
            geojson = GeoJSONParser(test_features.featurecollection_not_a_featurecollection)
        except Exception as e:
            pass
        self.assertTrue(isinstance(e, GeoJSONParserException))
        self.assertEqual(str(e), 'GeoJSON object must be of type FeatureCollection. The passed type was BunchaFeatures.')

    def test_no_features_member(self):
        try:
            geojson = GeoJSONParser(test_features.featurecollection_no_features_member)
        except Exception as e:
            pass
        self.assertTrue(isinstance(e, GeoJSONParserException))
        self.assertEqual(str(e), 'GeoJSON object must have member named "features" as an array of Features.')

    def test_bad_feature(self):
        try:
            geojson = GeoJSONParser(test_features.featurecollection_bad_feature)
        except Exception as e:
            pass
        self.assertTrue(isinstance(e, GeoJSONParserException))
        self.assertEqual(str(e), 'GeoJSON Features must have a type of "Feature" and "properties" and "geometry" members.')

    def test_bad_geometry_type(self):
        try:
            geojson = GeoJSONParser(test_features.featurecollection_bad_geometry_type)
        except Exception as e:
            pass
        self.assertTrue(isinstance(e, GeoJSONParserException))
        self.assertEqual(str(e), 'Rhombus is not a valid GeoJSON geometry.')

    def test_bad_geometry(self):
        try:
            geojson = GeoJSONParser(test_features.featurecollection_bad_geometry)
        except Exception as e:
            pass
        self.assertTrue(isinstance(e, GeoJSONParserException))
        self.assertEqual(str(e), 'GeoJSON validation error. Message: {0}'.format("Failed to validate field 'coordinates' list schema: Value -80.87088507656375 for list item is not of type array."))
