__author__ = 'amywieliczka, jblowe'

from django.conf.urls import patterns, url
from publicsearch import views

urlpatterns = patterns('',
                       url(r'^/?$', views.direct, name='direct'),
                       url(r'^publicsearch/$', views.publicsearch, name='publicsearch'),
                       url(r'^publicsearch/(?P<fieldfile>[\w-]+)$', views.loadNewFields, name='loadNewFields'),
                       url(r'^results/$', views.retrieveResults, name='retrieveResults'),
                       )
