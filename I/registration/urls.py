from django.conf.urls import patterns, include, url
 
urlpatterns = patterns('',
 
    url(r'^$', 'registration.views.registrate', name='registration'),
)