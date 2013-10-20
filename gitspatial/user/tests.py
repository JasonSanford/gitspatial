import json
import random
import string

from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.test import TestCase
from django.test.client import RequestFactory

from ..models import Repo, FeatureSet
from .views import user_repo, user_feature_set, user_repo_sync, user_repo_sync_status, user_feature_set_sync_status, user_feature_set_sync, user_landing


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

    def test_user_repo_sync_dne(self):
        request = self.factory.post('/user/repo/99999/sync')
        request.user = self.jason
        try:
            response = user_repo_sync(request, repo_id=99999)
        except Exception as exc:
            pass
        self.assertTrue(isinstance(exc, Http404))


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

    def test_user_sync_status_fs_dne(self):
        request = self.factory.get('/user/repo/99999/sync_status')
        request.user = self.jason
        try:
            response = user_repo_sync_status(request, repo_id=99999)
        except Exception as exc:
            pass
        self.assertTrue(isinstance(exc, Http404))


class UserFeatureSetSyncTest(TestCase):
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

    def test_user_can_sync_own_feature_set(self):
        request = self.factory.post('/user/feature_set/3/sync')
        request.user = self.jason
        response = user_feature_set_sync(request, feature_set_id=3)
        self.assertEqual(response.status_code, 201)

    def test_user_cannot_sync_others_feature_set(self):
        request = self.factory.post('/user/feature_set/19/sync')
        request.user = self.jason
        try:
            response = user_feature_set_sync(request, feature_set_id=19)
        except Exception as exc:
            pass
        self.assertTrue(isinstance(exc, PermissionDenied))

    def test_user_can_unsync_own_feature_set(self):
        request = self.factory.delete('/user/feature_set/3/sync')
        request.user = self.jason
        response = user_feature_set_sync(request, feature_set_id=3)
        self.assertEqual(response.status_code, 204)

    def test_user_cannot_unsync_others_feature_set(self):
        request = self.factory.delete('/user/feature_set/19/sync')
        request.user = self.jason
        try:
            response = user_feature_set_sync(request, feature_set_id=19)
        except Exception as exc:
            pass
        self.assertTrue(isinstance(exc, PermissionDenied))

    def test_invalid_method_put(self):
        request = self.factory.put('/user/feature_set/3/sync')
        request.user = self.jason
        response = user_feature_set_sync(request, feature_set_id=3)
        self.assertEqual(response.status_code, 405)

    def test_invalid_method_get(self):
        request = self.factory.get('/user/feature_set/3/sync')
        request.user = self.jason
        response = user_feature_set_sync(request, feature_set_id=3)
        self.assertEqual(response.status_code, 405)

    def test_feature_set_dne(self):
        request = self.factory.post('/user/feature_set/99999/sync')
        request.user = self.jason
        try:
            response = user_feature_set_sync(request, feature_set_id=99999)
        except Exception as exc:
            pass
        self.assertTrue(isinstance(exc, Http404))


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

    def test_user_sync_status_fs_dne(self):
        request = self.factory.get('/user/feature_set/99999/sync_status')
        request.user = self.jason
        try:
            response = user_feature_set_sync_status(request, feature_set_id=99999)
        except Exception as exc:
            pass
        self.assertTrue(isinstance(exc, Http404))


class PageViewTest(TestCase):
    fixtures = ['gitspatial/fixtures/test_data.json']

    def setUp(self):
        self.sal = User.objects.get(id=6)
        self.jason = User.objects.get(id=5)
        self.factory = RequestFactory()

    def test_user_landing(self):
        request = self.factory.get('/user')
        request.user = self.sal
        response = user_landing(request)
        self.assertEqual(response.status_code, 200)

    def test_user_cannot_view_others_repo(self):
        request = self.factory.get('/user/repo/22')
        request.user = self.sal
        response = user_repo(request, 22)
        self.assertEqual(response.status_code, 403)

    def test_user_can_view_own_repo(self):
        request = self.factory.get('/user/repo/22')
        request.user = self.jason
        response = user_repo(request, 22)
        self.assertEqual(response.status_code, 200)

    def test_user_cannot_view_others_feature_set(self):
        request = self.factory.get('/user/feature_set/3')
        request.user = self.sal
        response = user_feature_set(request, 3)
        self.assertEqual(response.status_code, 403)

    def test_user_can_view_own_feature_set(self):
        request = self.factory.get('/user/feature_set/3')
        request.user = self.jason
        response = user_feature_set(request, 3)
        self.assertEqual(response.status_code, 200)

    def test_feature_set_rename(self):
        request = self.factory.put('/user/feature_set/3', data='name=name&value=cats&pk=3')
        request.user = self.jason
        response = user_feature_set(request, 3)
        self.assertEqual(response.status_code, 200)

    def test_feature_set_rename_no_value(self):
        request = self.factory.put('/user/feature_set/3', data='name=name&pk=3')
        request.user = self.jason
        response = user_feature_set(request, 3)
        self.assertEqual(response.status_code, 400)

    def test_feature_set_rename_value_too_long(self):
        value = ''.join(random.choice(string.lowercase) for i in range(1003))
        request = self.factory.put('/user/feature_set/3', data='name=name&value={0}&pk=3'.format(value))
        request.user = self.jason
        response = user_feature_set(request, 3)
        self.assertEqual(response.status_code, 400)

    def test_page_too_high_redirects(self):
        request = self.factory.get('/user/feature_set/3?page=99999')
        request.user = self.jason
        response = user_feature_set(request, 3)
        self.assertEqual(response.status_code, 302)

    def test_string_page_redirects(self):
        request = self.factory.get('/user/feature_set/3?page=lobster')
        request.user = self.jason
        response = user_feature_set(request, 3)
        self.assertEqual(response.status_code, 302)

    def test_0_page_redirects(self):
        request = self.factory.get('/user/feature_set/3?page=0')
        request.user = self.jason
        response = user_feature_set(request, 3)
        self.assertEqual(response.status_code, 302)

    def test_feature_set_syncing(self):
        request = self.factory.get('/user/feature_set/3')
        fs = FeatureSet.objects.get(id=3)
        fs.sync_status = FeatureSet.SYNCING
        fs.save()
        request.user = self.jason
        response = user_feature_set(request, 3)
        self.assertEqual(response.status_code, 200)

    def test_unknown_repo_404s(self):
        # A 404 actually raises an exception, so we have to catch it to prove we 404'd. Lame.
        exc = None
        request = self.factory.get('/user/repo/99999')
        request.user = self.jason
        try:
            response = user_repo(request, 99999)
        except Exception as exc:
            pass
        self.assertTrue(isinstance(exc, Http404))

    def test_unknown_feature_set_404s(self):
        # A 404 actually raises an exception, so we have to catch it to prove we 404'd. Lame.
        exc = None
        request = self.factory.get('/user/feature_set/99999')
        request.user = self.jason
        try:
            response = user_feature_set(request, 99999)
        except Exception as exc:
            pass
        self.assertTrue(isinstance(exc, Http404))
