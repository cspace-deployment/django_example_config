__author__ = 'amywieliczka, jblowe'

from django.conf.urls import patterns, url
from osteology import views

urlpatterns = patterns('',
                       url(r'^/?$', views.direct, name='direct'),
                       url(r'^skeleton/$', views.skeleton, name='skeleton'),
                       url(r'^search/$', views.search, name='search'),
                       url(r'^results/$', views.retrieveResults, name='retrieveResults'),
                       )
