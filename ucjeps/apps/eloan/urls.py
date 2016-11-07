__author__ = 'jblowe, rjaffe'

from django.conf.urls import patterns, url
from eloan import views

urlpatterns = patterns('',
                       url(r'^/?', views.eloan, name='eloan'),
                       )
