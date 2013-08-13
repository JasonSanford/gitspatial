import json

import requests
from social_auth.models import UserSocialAuth


class GitHubApiRequest(object):
    _base_uri = 'https://api.github.com'

    def __init__(self, user, method, **kwargs):
        self._uri = self._base_uri + method

        social_auth_user = UserSocialAuth.objects.get(user=user, provider='github')
        social_extra = social_auth_user.extra_data
        access_token = social_extra['access_token']
        self._headers = {'Authorization': 'token {0}'.format(access_token)}


class GitHubApiGetRequest(GitHubApiRequest):
    def __init__(self, user, method):
        super(GitHubApiGetRequest, self).__init__(user, method)

        request = requests.get(self._uri, headers=self._headers)
        self.response = request


class GitHubApiPostRequest(GitHubApiRequest):
    def __init__(self, user, method, payload):
        kwargs = {'payload': payload}
        super(GitHubApiPostRequest, self).__init__(user, method, **kwargs)

        request = requests.post(self._uri, headers=self._headers, data=json.dumps(payload))
        self.response = request


class GitHubApiDeleteRequest(GitHubApiRequest):
    def __init__(self, user, method):
        super(GitHubApiDeleteRequest, self).__init__(user, method)

        request = requests.delete(self._uri, headers=self._headers)
        self.response = request
