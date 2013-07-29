import logging

from celery import task
import requests
from social_auth.models import UserSocialAuth


logger = logging.getLogger(__name__)


@task(name='get_user_repos')
def get_user_repos(user):
    social_auth_user = UserSocialAuth.objects.get(user=user, provider='github')
    social_extra = social_auth_user.extra_data
    access_token = social_extra['access_token']
    uri = 'https://api.github.com/user/repos'
    headers = {'Authorization': 'token {0}'.format(access_token)}
    request = requests.get(uri, headers=headers)
    logger.debug(request.json())
