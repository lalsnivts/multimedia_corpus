from django.conf.urls import patterns, include, url
from django.contrib import admin

urlpatterns = patterns('',
    # Examples:
    #url(r'^$', 'I.views.', name='home'),
    # url(r'^blog/', include('blog.urls')),
    ##url(r'^registration/', include('registration.urls')),
    url(r'^search/', include('search.urls')),
    url(r'^admin/', include(admin.site.urls)),
)
