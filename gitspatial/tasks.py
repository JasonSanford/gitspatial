import logging

from celery import task
from django.db.models.query import QuerySet
import requests
from social_auth.models import UserSocialAuth

from .models import Repo


logger = logging.getLogger(__name__)


@task(name='get_user_repos')
def get_user_repos(user_or_users):
    if isinstance(user_or_users, (list, tuple, QuerySet)):
        users = user_or_users
    else:
        users = [user_or_users]
    for user in users:
        social_auth_user = UserSocialAuth.objects.get(user=user, provider='github')
        social_extra = social_auth_user.extra_data
        access_token = social_extra['access_token']

        uri = 'https://api.github.com/user/repos'
        headers = {'Authorization': 'token {0}'.format(access_token)}
        request = requests.get(uri, headers=headers)

        raw_repos = request.json()
        for raw_repo in raw_repos:
            defaults = {
                'user': user,
                'name': raw_repo['name'],
                'full_name': raw_repo['full_name'],
                'private': raw_repo['private'],
            }
            repo, created = Repo.objects.get_or_create(github_id=raw_repo['id'], defaults=defaults)
            if created:
                logger.info('Created repo {0} for user {1}'.format(repo, user))
            else:
                repo.__dict__.update(defaults)
                repo.save()
                logger.info('Updated repo {0} for user {1}'.format(repo, user))
