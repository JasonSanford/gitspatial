from django.contrib.auth.models import User
from django.test import TestCase
from django.test.client import Client, RequestFactory

from .views import home
from .models import FeatureSet, Repo
from .test_geojson import featurecollection_with_zs, featurecollection_no_zs
from .utils import strip_zs


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

class ModelsTest(TestCase):
    fixtures = ['gitspatial/fixtures/test_data.json']

    def setUp(self):
        self.fs = FeatureSet.objects.get(id=3)
        self.fs2 = FeatureSet.objects.get(id=18)
        self.repo = Repo.objects.get(id=22)

    def test_feature_set_is_syncing_false(self):
        self.assertEqual(self.fs.is_syncing, False)

    def test_feature_set_is_syncing_true(self):
        self.fs.synced = True
        self.fs.sync_status = self.fs.SYNCING
        self.fs.save()
        self.assertEqual(self.fs.is_syncing, True)

    def test_repo_is_syncing_false(self):
        self.assertEqual(self.repo.is_syncing, False)

    def test_repo_is_syncing_true(self):
        self.repo.sync_status = self.fs.SYNCING
        self.repo.save()
        self.assertEqual(self.repo.is_syncing, True)

    def test_repo_size_pretty(self):
        self.assertEqual(self.fs.size_pretty, '3.4 KB')
        self.assertEqual(self.fs2.size_pretty, '6.4 KB')

    def test_repo_hook_url(self):
        self.assertEqual(self.repo.hook_url, 'http://gitspatial.com/api/v1/hooks/22')

    def test_feature_set_center(self):
        self.assertEqual(self.fs.center, (-80.82542950000001, 35.283412999999996))

    def test_feature_set_bounds(self):
        self.assertEqual(self.fs.bounds, (-80.955914, 35.067714, -80.694945, 35.499112))


class StripZTest(TestCase):
    def setUp(self):
        pass

    def test_z_values_stripped(self):
        new_featurecollection = {'type': 'FeatureCollection', 'features': []}

        for feature in featurecollection_with_zs['features']:
            feature['geometry'] = strip_zs(feature['geometry'])
            new_featurecollection['features'].append(feature)

        self.assertEqual(new_featurecollection, featurecollection_no_zs)
