import base64
import json
import logging

from celery import task
from django.contrib.gis.geos import GEOSGeometry
from django.contrib.gis.geos.error import GEOSException
from django.db.models.query import QuerySet

from .models import Repo, FeatureSet, Feature
from .github import GitHub
from .geojson import GeoJSONParser, GeoJSONParserException
from .utils import strip_zs


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
        github = GitHub(user)
        current_repos = []
        api_path = '/user/repos'
        there_are_more_repos = True
        while there_are_more_repos:
            gh_request = github.get(api_path)
            if hasattr(gh_request, 'links') and 'next' in gh_request.links:
                next_url = gh_request.links['next']['url']
                next_url_parts = next_url.split('api.github.com')
                api_path = next_url_parts[1]
            else:
                there_are_more_repos = False
            for raw_repo in gh_request.json():
                try:
                    defaults = {
                        'user': user,
                        'name': raw_repo['name'],
                        'full_name': raw_repo['full_name'],
                        'github_private': raw_repo['private'],
                        'master_branch': raw_repo['master_branch'],
                    }
                except KeyError:
                    # Repos without commits have no master_branch. seeya.
                    logger.warning('Repo has no master_branch key: %s' % raw_repo['full_name'])
                    continue
                repo, created = Repo.objects.get_or_create(github_id=raw_repo['id'], defaults=defaults)
                current_repos.append(repo)
                if created:
                    logger.info('Created repo {0} for user {1}'.format(repo, user))
                else:
                    repo.__dict__.update(defaults)
                    repo.save()
                    logger.info('Updated repo {0} for user {1}'.format(repo, user))
        for previous_repo in previous_repos:
            if previous_repo not in current_repos:
                previous_repo.delete()


@task(name='get_repo_feature_sets')
def get_repo_feature_sets(repo_or_repos, sync_feature_sets=True):
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
        github = GitHub(repo.user)
        current_feature_sets = []
        gh_request = github.get('/repos/{0}/git/trees/master?recursive=1'.format(repo.full_name))
        for item in gh_request.json()['tree']:
            if item['type'] == 'blob' and item['path'].endswith('.geojson'):
                defaults = {'name': item['path'], 'size': item['size']}
                feature_set, created = FeatureSet.objects.get_or_create(repo=repo, path=item['path'], defaults=defaults)
                current_feature_sets.append(feature_set)
                if feature_set.synced and sync_feature_sets:
                    logger.info('Setting feature set sync status as syncing: {0}'.format(feature_set))
                    feature_set.sync_status = FeatureSet.SYNCING
                    feature_set.save()
                    get_feature_set_features.apply_async((feature_set,))
        for previous_feature_set in previous_feature_sets:
            if previous_feature_set not in current_feature_sets:
                previous_feature_set.delete()
        logger.info('Setting repo sync status as synced: {0}'.format(repo))
        repo.sync_status = Repo.SYNCED
        repo.save()


@task(name='get_feature_set_features')
def get_feature_set_features(feature_set_or_feature_sets):
    """
    Delete all features for, and create
    features for a feature set
    """
    one_megabyte = 1048576
    if isinstance(feature_set_or_feature_sets, (list, tuple, QuerySet)):
        feature_sets = feature_set_or_feature_sets
    else:
        feature_sets = [feature_set_or_feature_sets]
    for feature_set in feature_sets:
        # First, kill the current features
        if not feature_set.synced:
            return
        logger.info('Setting feature set sync status as syncing: {0}'.format(feature_set))
        feature_set.sync_status = feature_set.SYNCING
        feature_set.save()
        Feature.objects.filter(feature_set=feature_set).delete()
        github = GitHub(feature_set.repo.user)
        if feature_set.size < one_megabyte:
            # We can get files < 1 megabyte via the Repo API
            gh_request = github.get('/repos/{0}/contents/{1}'.format(feature_set.repo.full_name, feature_set.path))
            content = base64.b64decode(gh_request.json()['content'])
        else:
            # For files > 1 megabyte, we have to a lot of HTTP dancing
            try:
                content = _get_blob(github, feature_set)
            except MemoryError:
                logger.error('MemoryError parsing FeatureSet: {0}'.format(feature_set))
                logger.info('Setting feature set sync status as error syncing: {0}'.format(feature_set))
                feature_set.sync_status = FeatureSet.MEMORY_ERROR
                feature_set.save()
                return
        try:
            geojson = GeoJSONParser(content)
        except GeoJSONParserException as e:
            logger.error('GeoJSONParserError parsing FeatureSet: {0} with error: {1}'.format(feature_set, e))
            logger.info('Setting feature set sync status as error syncing: {0}'.format(feature_set))
            feature_set.sync_status = FeatureSet.ERROR_SYNCING
            feature_set.save()
            return
        for feature in geojson.features:
            geojson_geometry = strip_zs(feature['geometry'])
            try:
                geom = GEOSGeometry(json.dumps(geojson_geometry))
            except GEOSException:
                logger.error('Could not parse as GEOSGeometry: %s' % geojson_geometry)
                # This one feature failed, but let's process the rest.
                continue
            properties = json.dumps(feature['properties'])
            feature = Feature(feature_set=feature_set, geom=geom, properties=properties)
            feature.save()
            logger.debug('Created Feature: {0}'.format(feature))
        logger.info('Setting feature set sync status as synced: {0}'.format(feature_set))
        feature_set.sync_status = FeatureSet.SYNCED
        feature_set.save()


@task(name='delete_repo_feature_sets')
def delete_repo_feature_sets(repo):
    logger.info('Deleting feature sets for repo: {0}'.format(repo))
    FeatureSet.objects.filter(repo=repo).delete()


@task(name='delete_feature_set_features')
def delete_feature_set_features(feature_set):
    logger.info('Deleting features for feature set: {0}'.format(feature_set))
    Feature.objects.filter(feature_set=feature_set).delete()


def _get_blob(github, feature_set):
    # Get the head of the master branch
    head_request = github.get('/repos/{0}/git/refs/heads/{1}'.format(feature_set.repo.full_name, feature_set.repo.master_branch))

    # Get the latest commit  in this branch
    commit_request = github.get(head_request.json()['object']['url'].split('github.com')[1])

    # Get the tree from the latest commit
    tree_request = github.get(commit_request.json()['tree']['url'].split('github.com')[1] + '?recursive=1')
    blob_url = None
    for item in tree_request.json()['tree']:
        if item['path'] == feature_set.path:
            blob_url = item['url'].split('github.com')[1]
            continue

    # Get the blob
    try:
        blob_request = github.get(blob_url)
        encoded_content = blob_request.json()['content']
        decoded = base64.b64decode(encoded_content)
    except MemoryError:
        raise
    return decoded
