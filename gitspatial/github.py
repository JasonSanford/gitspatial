import json

import requests
from social_auth.models import UserSocialAuth


class GitHub(object):
    _base_uri = 'https://api.github.com'

    def __init__(self, user):
        social_auth_user = UserSocialAuth.objects.get(user=user, provider='github')
        social_extra = social_auth_user.extra_data
        access_token = social_extra['access_token']
        self._headers = {'Authorization': 'token {0}'.format(access_token)}

    def get(self, method):
        return requests.get(self._base_uri + method, headers=self._headers)

    def post(self, method, payload):
        return requests.post(self._base_uri + method, headers=self._headers, data=json.dumps(payload))

    def delete(self, method):
        return requests.delete(self._base_uri + method, headers=self._headers)
