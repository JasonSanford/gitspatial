from django.contrib.auth.models import User
from django.test import TestCase
from django.test.client import Client, RequestFactory

from gitspatial.views import home


class WebTest(TestCase):
    fixtures = ['gitspatial/fixtures/test_data.json']

    def setUp(self):
        self.client = Client()
        self.factory = RequestFactory()
        self.jason = User.objects.get(id=5)

    def test_home(self):
        request = self.client.get('/')
        self.assertEqual(request.status_code, 200)

    def test_home_redirects_to_user(self):
        request = self.factory.get('/')
        request.user = self.jason
        response = home(request)
        self.assertEqual(response.status_code, 302)
