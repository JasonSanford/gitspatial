from django.conf.urls import patterns, include, url

urlpatterns = patterns('gitspatial.user.views',
    url(r'^$', 'user_landing', name='user_landing'),
    url(r'repo/(?P<repo_id>\d+)$', 'user_repo', name='user_repo'),
    url(r'feature_set/(?P<feature_set_id>\d+)$', 'user_feature_set', name='user_feature_set'),
    url(r'repo/(?P<repo_id>\d+)/sync$', 'user_repo_sync', name='user_repo_sync'),
    url(r'repo/(?P<repo_id>\d+)/sync_status$', 'user_repo_sync_status', name='user_repo_sync_status'),
    url(r'feature_set/(?P<feature_set_id>\d+)/sync$', 'user_feature_set_sync', name='user_feature_set_sync'),
)
