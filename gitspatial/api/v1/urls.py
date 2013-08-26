from django.conf.urls import patterns, include, url

urlpatterns = patterns('gitspatial.api.v1.views',
    url(r'^$', 'docs', name='v1_api_docs'),
    url(r'^hooks/(?P<repo_id>\d+)$', 'repo_hook', name='v1_repo_hook'),
    url(r'^(?P<user_name>[.a-zA-Z0-9_-]*)/(?P<repo_name>[.a-zA-Z0-9_-]*)/(?P<feature_set_name>.*)', 'feature_set_query', name='v1_feature_set_query'),
)
