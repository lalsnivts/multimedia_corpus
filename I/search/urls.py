from django.conf.urls import patterns, include, url
 
urlpatterns = patterns('',
 
    url(r'^$', 'search.views.search', name='contact'),
    url(r'^ex$', 'search.views.ex',name='working_station'),
    url(r'^ket_ex', 'search.views.ket_ex',name='working_station'),
)