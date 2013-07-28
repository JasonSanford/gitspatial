from django.conf import settings
from django.conf.urls import patterns, include, url
from social_auth.views import auth

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', 'gitspatial.views.home', name='home'),
    # Examples:
    # url(r'^gitspatial/', include('gitspatial.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
    url(r'^login/$', auth, kwargs={'backend': 'github'}, name='login'),
    url(r'^logout/$', 'gitspatial.views.logout', name='logout'),
    url(r'^user/$', 'gitspatial.views.user_landing', name='user_landing'),
    url(r'', include('social_auth.urls')),
)

if settings.DEBUG:
    urlpatterns += patterns('django.contrib.staticfiles.views',
        url(r'^static/(?P<path>.*)$', 'serve'),
    )
