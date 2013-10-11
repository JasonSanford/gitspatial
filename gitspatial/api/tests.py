import json
import logging

from django.test import TestCase
from django.test.client import Client

from .exceptions import InvalidSpatialParameterException
from .helpers import query_args

# Simma down the logs during testing
logger = logging.getLogger('gitspatial.api.v1.views')
logger.setLevel(logging.ERROR)

class APIRequestTest(TestCase):
    fixtures = ['gitspatial/fixtures/test_data.json']

    def setUp(self):
        self.client = Client()

    def test_bbox(self):
        response = self.client.get('/api/v1/JasonSanford/mecklenburg-gis-opendata/data/colleges.geojson?bbox=-80.888,35.206,-80.799,35.270')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        json_content = json.loads(response.content)
        self.assertEqual(len(json_content['features']), 7)

    def test_all_features(self):
        response = self.client.get('/api/v1/JasonSanford/mecklenburg-gis-opendata/data/colleges.geojson')
        self.assertEqual(response.status_code, 200)
        json_content = json.loads(response.content)
        self.assertEqual(len(json_content['features']), 26)

    def test_bbox_too_many_coords(self):
        response = self.client.get('/api/v1/JasonSanford/mecklenburg-gis-opendata/data/colleges.geojson?bbox=-80.888,35.206,-80.799,35.270,99')
        self.assertEqual(response.status_code, 400)
        json_content = json.loads(response.content)
        expected = {
            'status': 'error',
            'message': 'The bbox parameter must contain 4 items: xmin, ymin, xmax, ymax'
        }
        self.assertEqual(json_content, expected)

    def test_bbox_non_floatable(self):
        response = self.client.get('/api/v1/JasonSanford/mecklenburg-gis-opendata/data/colleges.geojson?bbox=lobster,4,cat,8')
        self.assertEqual(response.status_code, 400)
        json_content = json.loads(response.content)
        expected = {
            'status': 'error',
            'message': 'Items in the bbox parameter must be parseable as floats'
        }
        self.assertEqual(json_content, expected)

    def test_jsonp(self):
        response = self.client.get('/api/v1/JasonSanford/mecklenburg-gis-opendata/data/colleges.geojson?bbox=-80.84761,35.23020,-80.84629,35.23110&callback=myFunc')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/javascript')
        self.assertEqual(response.content[:7], 'myFunc(')
        self.assertEqual(response.content[-1], ')')

    def test_within_distance(self):
        response = self.client.get('/api/v1/JasonSanford/mecklenburg-gis-opendata/data/polling_locations.geojson?lat=35.1889&lon=-80.7870&distance=3000')
        self.assertEqual(response.status_code, 200)
        json_content = json.loads(response.content)
        self.assertEqual(len(json_content['features']), 10)

    def test_within_distance_bad_parameters(self):
        response = self.client.get('/api/v1/JasonSanford/mecklenburg-gis-opendata/data/polling_locations.geojson?lat=cat&lon=-80.7870&distance=3000')
        self.assertEqual(response.status_code, 400)
        json_content = json.loads(response.content)
        expected = {
            'status': 'error',
            'message': 'Parameters lat, lon and distance must be parseable as floats'
        }
        self.assertEqual(json_content, expected)


class PaginationTest(TestCase):
    fixtures = ['gitspatial/fixtures/test_data.json']

    def setUp(self):
        self.client = Client()

    def test_pagination_defaults(self):
        response = self.client.get('/api/v1/JasonSanford/mecklenburg-gis-opendata/data/polling_locations.geojson')
        self.assertEqual(response.status_code, 200)
        json_content = json.loads(response.content)
        self.assertEqual(len(json_content['features']), 150)

    def test_pagination_custom_limit(self):
        response = self.client.get('/api/v1/JasonSanford/mecklenburg-gis-opendata/data/polling_locations.geojson?limit=30')
        self.assertEqual(response.status_code, 200)
        json_content = json.loads(response.content)
        self.assertEqual(len(json_content['features']), 30)

    def test_pagination_custom_limit_offset(self):
        response = self.client.get('/api/v1/JasonSanford/mecklenburg-gis-opendata/data/polling_locations.geojson?limit=30&offset=30')
        self.assertEqual(response.status_code, 200)
        json_content = json.loads(response.content)
        self.assertEqual(len(json_content['features']), 30)

    def test_bbox_with_limit_greater_than_set(self):
        response = self.client.get('/api/v1/JasonSanford/mecklenburg-gis-opendata/data/colleges.geojson?bbox=-80.888,35.206,-80.799,35.270&limit=20')
        self.assertEqual(response.status_code, 200)
        json_content = json.loads(response.content)
        self.assertEqual(len(json_content['features']), 7)

    def test_bbox_with_limit_less_than_set(self):
        response = self.client.get('/api/v1/JasonSanford/mecklenburg-gis-opendata/data/colleges.geojson?bbox=-80.888,35.206,-80.799,35.270&limit=5')
        self.assertEqual(response.status_code, 200)
        json_content = json.loads(response.content)
        self.assertEqual(len(json_content['features']), 5)

    def test_within_distance_limit(self):
        response = self.client.get('/api/v1/JasonSanford/mecklenburg-gis-opendata/data/polling_locations.geojson?lat=35.1889&lon=-80.7870&distance=3000&limit=3')
        self.assertEqual(response.status_code, 200)
        json_content = json.loads(response.content)
        self.assertEqual(len(json_content['features']), 3)


class PaginationMembersTest(TestCase):
    fixtures = ['gitspatial/fixtures/test_data.json']

    def setUp(self):
        self.client = Client()

    def test_with_limit(self):
        response = self.client.get('/api/v1/JasonSanford/mecklenburg-gis-opendata/data/polling_locations.geojson?limit=25')
        json_content = json.loads(response.content)
        count = json_content['count']
        total_count = json_content['total_count']
        self.assertEqual(count, 25)
        self.assertEqual(total_count, 150)

    def test_without_limit(self):
        response = self.client.get('/api/v1/JasonSanford/mecklenburg-gis-opendata/data/polling_locations.geojson')
        json_content = json.loads(response.content)
        count = json_content['count']
        total_count = json_content['total_count']
        self.assertEqual(count, 150)
        self.assertEqual(total_count, 150)

    def test_count_less_than_limit(self):
        response = self.client.get('/api/v1/JasonSanford/mecklenburg-gis-opendata/data/polling_locations.geojson?limit=10&offset=145')
        json_content = json.loads(response.content)
        count = json_content['count']
        total_count = json_content['total_count']
        self.assertEqual(count, 5)
        self.assertEqual(total_count, 150)


class HttpMethodTest(TestCase):
    fixtures = ['gitspatial/fixtures/test_data.json']

    def setUp(self):
        self.client = Client()

    def test_get(self):
        response = self.client.get('/api/v1/JasonSanford/mecklenburg-gis-opendata/data/polling_locations.geojson')
        self.assertEqual(response.status_code, 200)

    def test_put(self):
        response = self.client.put('/api/v1/JasonSanford/mecklenburg-gis-opendata/data/polling_locations.geojson')
        self.assertEqual(response.status_code, 405)

    def test_post(self):
        response = self.client.post('/api/v1/JasonSanford/mecklenburg-gis-opendata/data/polling_locations.geojson')
        self.assertEqual(response.status_code, 405)

    def test_delete(self):
        response = self.client.delete('/api/v1/JasonSanford/mecklenburg-gis-opendata/data/polling_locations.geojson')
        self.assertEqual(response.status_code, 405)


# Query Prameters
class BBoxTest(TestCase):
    def setUp(self):
        pass

    def test_3_items(self):
        exc = None
        try:
            query_args.by_bbox('1,2,3')
        except Exception as exc:
            pass
        self.assertTrue(isinstance(exc, InvalidSpatialParameterException))
        self.assertEqual(str(exc), 'The bbox parameter must contain 4 items: xmin, ymin, xmax, ymax')

    def test_non_floatable(self):
        exc = None
        try:
            query_args.by_bbox('1,2,3,lobster')
        except Exception as exc:
            pass
        self.assertTrue(isinstance(exc, InvalidSpatialParameterException))
        self.assertEqual(str(exc), 'Items in the bbox parameter must be parseable as floats')
