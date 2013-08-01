import logging

from celery import task
from django.db.models.query import QuerySet

from .models import Repo, FeatureSet
from .github import GitHubApiGetRequest


logger = logging.getLogger(__name__)


@task(name='get_user_repos')
def get_user_repos(user_or_users):
    """
    Create or update the repos for a single
    user or set of users
    """
    logging.debug('got here')
    if isinstance(user_or_users, (list, tuple, QuerySet)):
        users = user_or_users
    else:
        users = [user_or_users]
    for user in users:
        raw_repos = GitHubApiGetRequest(user, '/user/repos')
        for raw_repo in raw_repos.json:
            defaults = {
                'user': user,
                'name': raw_repo['name'],
                'full_name': raw_repo['full_name'],
                'github_private': raw_repo['private'],
            }
            repo, created = Repo.objects.get_or_create(github_id=raw_repo['id'], defaults=defaults)
            if created:
                logger.info('Created repo {0} for user {1}'.format(repo, user))
            else:
                repo.__dict__.update(defaults)
                repo.save()
                logger.info('Updated repo {0} for user {1}'.format(repo, user))
            if repo.synced:
                get_repo_feature_sets.apply_async((repo,))


@task(name='get_repo_feature_sets')
def get_repo_feature_sets(repo_or_repos):
    """
    Create or update the feature sets for
    a single repo or set of repos
    """
    if isinstance(repo_or_repos, (list, tuple, QuerySet)):
        repos = repo_or_repos
    else:
        repos = [repo_or_repos]
    for repo in repos:
        previous_feature_sets = FeatureSet.objects.filter(repo=repo)
        current_feature_sets = []
        raw_contents = GitHubApiGetRequest(repo.user, '/repos/{0}/contents/'.format(repo.full_name))
        for item in raw_contents.json:
            if item['type'] == 'file' and item['name'].endswith('.geojson'):
                defaults = {'name': item['name'][:item['name'].find('.geojson')]}
                feature_set, created = FeatureSet.objects.get_or_create(repo=repo, file_name=item['name'], defaults=defaults)
                current_feature_sets.append(feature_set)
        for previous_feature_set in previous_feature_sets:
            if previous_feature_set not in current_feature_sets:
                previous_feature_set.delete()


@task(name='delete_repo_feature_sets')
def delete_repo_feature_sets(repo):
    logger.info('Deleting feature sets for repo: {0}'.format(repo))
    feature_sets = FeatureSet.objects.filter(repo=repo)
    for feature_set in feature_sets:
        logger.info('Deleting feature set: {0}'.format(feature_set))
        feature_set.delete()
