__author__ = 'jblowe'

from django.conf.urls import patterns, url
from locationhistory import views

urlpatterns = patterns('',
                       url(r'^$', views.index, name='index'),
                       )