import json

from django.contrib.auth.models import User
from django.test import TestCase
from django.test.client import RequestFactory

from ..models import Repo, FeatureSet
from .views import user_repo_sync, user_repo_sync_status, user_feature_set_sync_status


class UserRepoSyncTest(TestCase):
    #
    # These are kind of terrible now. They test for a forbidden response is
    # legit, but we're short circuiting the POST to sync as to not make
    # an external request to GitHub.
    #
    fixtures = ['gitspatial/fixtures/test_data.json']

    def setUp(self):
        self.sal = User.objects.get(id=6)
        self.jason = User.objects.get(id=5)
        self.factory = RequestFactory()

    def test_user_can_sync_own_repo(self):
        request = self.factory.post('/user/repo/22/sync?testing=1')
        request.user = self.jason
        response = user_repo_sync(request, repo_id=22)
        self.assertEqual(response.status_code, 201)

    def test_user_cannot_sync_others_repo(self):
        request = self.factory.post('/user/repo/22/sync')
        request.user = self.sal
        response = user_repo_sync(request, repo_id=22)
        self.assertEqual(response.status_code, 403)

    def test_user_can_unsync_own_repo(self):
        request = self.factory.delete('/user/repo/22/sync?testing=1')
        request.user = self.jason
        response = user_repo_sync(request, repo_id=22)
        self.assertEqual(response.status_code, 204)

    def test_user_cannot_unsync_others_repo(self):
        request = self.factory.delete('/user/repo/22/sync')
        request.user = self.sal
        response = user_repo_sync(request, repo_id=22)
        self.assertEqual(response.status_code, 403)

    def test_invalid_method_put(self):
        request = self.factory.put('/user/repo/22/sync?testing=1')
        request.user = self.jason
        response = user_repo_sync(request, repo_id=22)
        self.assertEqual(response.status_code, 405)

    def test_invalid_method_get(self):
        request = self.factory.get('/user/repo/22/sync?testing=1')
        request.user = self.jason
        response = user_repo_sync(request, repo_id=22)
        self.assertEqual(response.status_code, 405)


class UserRepoSyncStatusTest(TestCase):
    fixtures = ['gitspatial/fixtures/test_data.json']

    def setUp(self):
        self.sal = User.objects.get(id=6)
        self.jason = User.objects.get(id=5)
        self.factory = RequestFactory()
        self.a_synced_repo = Repo.objects.get(id=22)

    def test_user_can_sync_status_own_repo(self):
        request = self.factory.get('/user/repo/22/sync_status')
        request.user = self.jason
        response = user_repo_sync_status(request, repo_id=22)
        self.assertEqual(response.status_code, 200)

    def test_user_cannot_sync_status_others_repo(self):
        request = self.factory.get('/user/repo/22/sync_status')
        request.user = self.sal
        response = user_repo_sync_status(request, repo_id=22)
        self.assertEqual(response.status_code, 403)

    def test_user_sync_status_synced(self):
        self.a_synced_repo.sync_status = self.a_synced_repo.SYNCED
        self.a_synced_repo.save()
        request = self.factory.get('/user/repo/22/sync_status')
        request.user = self.jason
        response = user_repo_sync_status(request, repo_id=22)
        expected = {'status': 'synced'}
        self.assertEqual(json.loads(response.content), expected)

    def test_user_sync_status_syncing(self):
        self.a_synced_repo.sync_status = self.a_synced_repo.SYNCING
        self.a_synced_repo.save()
        request = self.factory.get('/user/repo/22/sync_status')
        request.user = self.jason
        response = user_repo_sync_status(request, repo_id=22)
        expected = {'status': 'syncing'}
        self.assertEqual(json.loads(response.content), expected)

    def test_user_sync_status_not_synced(self):
        self.a_synced_repo.sync_status = self.a_synced_repo.NOT_SYNCED
        self.a_synced_repo.save()
        request = self.factory.get('/user/repo/22/sync_status')
        request.user = self.jason
        response = user_repo_sync_status(request, repo_id=22)
        expected = {'status': 'not_synced'}
        self.assertEqual(json.loads(response.content), expected)

    def test_user_sync_status_error(self):
        self.a_synced_repo.sync_status = self.a_synced_repo.ERROR_SYNCING
        self.a_synced_repo.save()
        request = self.factory.get('/user/repo/22/sync_status')
        request.user = self.jason
        response = user_repo_sync_status(request, repo_id=22)
        expected = {'status': 'error'}
        self.assertEqual(json.loads(response.content), expected)


class UserFeatureSetSyncStatusTest(TestCase):
    fixtures = ['gitspatial/fixtures/test_data.json']

    def setUp(self):
        self.sal = User.objects.get(id=6)
        self.jason = User.objects.get(id=5)
        self.factory = RequestFactory()
        self.fs = FeatureSet.objects.get(id=18)

    def test_user_can_sync_status_own_repo(self):
        request = self.factory.get('/user/feature_set/18/sync_status')
        request.user = self.jason
        response = user_feature_set_sync_status(request, feature_set_id=18)
        self.assertEqual(response.status_code, 200)

    def test_user_cannot_sync_status_others_repo(self):
        request = self.factory.get('/user/feature_set/18/sync_status')
        request.user = self.sal
        response = user_feature_set_sync_status(request, feature_set_id=18)
        self.assertEqual(response.status_code, 403)

    def test_user_sync_status_synced(self):
        self.fs.sync_status = self.fs.SYNCED
        self.fs.save()
        request = self.factory.get('/user/feature_set/18/sync_status')
        request.user = self.jason
        response = user_feature_set_sync_status(request, feature_set_id=18)
        expected = {'status': 'synced'}
        self.assertEqual(json.loads(response.content), expected)

    def test_user_sync_status_syncing(self):
        self.fs.sync_status = self.fs.SYNCING
        self.fs.save()
        request = self.factory.get('/user/feature_set/18/sync_status')
        request.user = self.jason
        response = user_feature_set_sync_status(request, feature_set_id=18)
        expected = {'status': 'syncing'}
        self.assertEqual(json.loads(response.content), expected)

    def test_user_sync_status_not_synced(self):
        self.fs.sync_status = self.fs.NOT_SYNCED
        self.fs.save()
        request = self.factory.get('/user/feature_set/18/sync_status')
        request.user = self.jason
        response = user_feature_set_sync_status(request, feature_set_id=18)
        expected = {'status': 'not_synced'}
        self.assertEqual(json.loads(response.content), expected)

    def test_user_sync_status_error(self):
        self.fs.sync_status = self.fs.ERROR_SYNCING
        self.fs.save()
        request = self.factory.get('/user/feature_set/18/sync_status')
        request.user = self.jason
        response = user_feature_set_sync_status(request, feature_set_id=18)
        expected = {'status': 'error'}
        self.assertEqual(json.loads(response.content), expected)
