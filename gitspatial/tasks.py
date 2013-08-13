import base64
import json
import logging

from celery import task
from django.contrib.gis.geos import GEOSGeometry
from django.db.models.query import QuerySet

from .models import Repo, FeatureSet, Feature
from .github import GitHubApiGetRequest
from .geojson import GeoJSONParser, GeoJSONParserException


logger = logging.getLogger(__name__)


@task(name='get_user_repos')
def get_user_repos(user_or_users):
    """
    Create or update the repos for a single
    user or set of users
    """
    if isinstance(user_or_users, (list, tuple, QuerySet)):
        users = user_or_users
    else:
        users = [user_or_users]
    for user in users:
        previous_repos = Repo.objects.filter(user=user)
        current_repos = []
        api_path = '/user/repos'
        there_are_more_repos = True
        while there_are_more_repos:
            gh_request = GitHubApiGetRequest(user, api_path)
            if hasattr(gh_request.response, 'links') and 'next' in gh_request.response.links:
                next_url = gh_request.response.links['next']['url']
                next_url_parts = next_url.split('api.github.com')
                api_path = next_url_parts[1]
            else:
                there_are_more_repos = False
            for raw_repo in gh_request.response.json():
                defaults = {
                    'user': user,
                    'name': raw_repo['name'],
                    'full_name': raw_repo['full_name'],
                    'github_private': raw_repo['private'],
                }
                repo, created = Repo.objects.get_or_create(github_id=raw_repo['id'], defaults=defaults)
                current_repos.append(repo)
                if created:
                    logger.info('Created repo {0} for user {1}'.format(repo, user))
                else:
                    repo.__dict__.update(defaults)
                    repo.save()
                    logger.info('Updated repo {0} for user {1}'.format(repo, user))
                if repo.synced:
                    get_repo_feature_sets.apply_async((repo,))
        for previous_repo in previous_repos:
            if previous_repo not in current_repos:
                previous_repo.delete()


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
        gh_request = GitHubApiGetRequest(repo.user, '/repos/{0}/git/trees/master?recursive=1'.format(repo.full_name))
        for item in gh_request.response.json()['tree']:
            if item['type'] == 'blob' and item['path'].endswith('.geojson'):
                defaults = {'name': item['path']}
                feature_set, created = FeatureSet.objects.get_or_create(repo=repo, path=item['path'], defaults=defaults)
                current_feature_sets.append(feature_set)
                if feature_set.synced:
                    get_feature_set_features.apply_async((feature_set,))
        for previous_feature_set in previous_feature_sets:
            if previous_feature_set not in current_feature_sets:
                previous_feature_set.delete()


@task(name='get_feature_set_features')
def get_feature_set_features(feature_set_or_feature_sets):
    """
    Delete all features for, and create
    features for a feature set
    """
    if isinstance(feature_set_or_feature_sets, (list, tuple, QuerySet)):
        feature_sets = feature_set_or_feature_sets
    else:
        feature_sets = [feature_set_or_feature_sets]
    for feature_set in feature_sets:
        # First, kill the current features
        if not feature_set.synced:
            return
        Feature.objects.filter(feature_set=feature_set).delete()
        gh_request = GitHubApiGetRequest(
            feature_set.repo.user,
            '/repos/{0}/contents/{1}'.format(feature_set.repo.full_name, feature_set.path))
        content = base64.b64decode(gh_request.response.json()['content'])
        try:
            geojson = GeoJSONParser(content)
        except GeoJSONParserException as e:
            logger.error('GeoJSONParserError parsing FeatureSet: {0} with error: {1}'.format(feature_set, e))
            return
        for feature in geojson.features:
            geom = GEOSGeometry(json.dumps(feature['geometry']))
            properties = json.dumps(feature['properties'])
            feature = Feature(feature_set=feature_set, geom=geom, properties=properties)
            feature.save()
            logger.info('Created Feature: {0}'.format(feature))


@task(name='delete_repo_feature_sets')
def delete_repo_feature_sets(repo):
    logger.info('Deleting feature sets for repo: {0}'.format(repo))
    FeatureSet.objects.filter(repo=repo).delete()


@task(name='delete_feature_set_features')
def delete_feature_set_features(feature_set):
    logger.info('Deleting features for feature set: {0}'.format(feature_set))
    Feature.objects.filter(feature_set=feature_set).delete()
