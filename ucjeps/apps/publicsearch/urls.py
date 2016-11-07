__author__ = 'amywieliczka, jblowe'

from django.conf.urls import patterns, url
from publicsearch import views

urlpatterns = patterns('',
                       url(r'^/?$', views.direct, name='direct'),
                       url(r'^publicsearch/$', views.publicsearch, name='publicSearch'),
                       url(r'^embedded/$', views.embeddedsearch, name='embedded'),
                       url(r'^results/$', views.retrieveResults, name='retrieveResults'),
                       url(r'^bmapper/$', views.bmapper, name='bmapper'),
                       url(r'^csv/$', views.csv, name='csv'),
                       url(r'^gmapper/$', views.gmapper, name='gmapper'),
                       )