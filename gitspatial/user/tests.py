from django.test import TestCase


class APITest(TestCase):
    def setUp(self):
        pass

    def test_foo(self):
        self.assertEqual(1, 1)

    def test_bar(self):
        self.assertEqual('lobster', 'lobster')
