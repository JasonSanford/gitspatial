from django.test import TestCase

from .exceptions import InvalidSpatialParameterException
from .helpers import query_args


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
