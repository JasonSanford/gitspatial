from django.conf.urls import patterns, include, url

urlpatterns = patterns('gitspatial.user.views',
    url(r'^$', 'user_landing', name='user_landing'),
    url(r'repo/(?P<repo_id>\d+)$', 'repo_sync', name='repo_sync'),
)
