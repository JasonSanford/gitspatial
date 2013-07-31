from django.conf.urls import patterns, include, url

urlpatterns = patterns('gitspatial.user.views',
    url(r'^$', 'user_landing', name='user_landing'),
    url(r'repo/(?P<repo_id>\d+)$', 'user_repo', name='user_repo'),
    url(r'repo/(?P<repo_id>\d+)/sync$', 'user_repo_sync', name='user_repo_sync'),
)
