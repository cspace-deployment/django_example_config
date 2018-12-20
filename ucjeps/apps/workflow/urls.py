__author__ = 'jblowe'

from django.conf.urls import patterns, url
from workflow import views

urlpatterns = patterns('',
                       url(r'^/?$', views.workflow, name='index'),
                       url(r'^(?P<page>[\w\-\.]+)?$', views.workflow, name='index')
                       )
