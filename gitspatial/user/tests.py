from django.contrib.auth.models import User
from django.test import TestCase
from django.test.client import RequestFactory

from .views import user_repo_sync


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
