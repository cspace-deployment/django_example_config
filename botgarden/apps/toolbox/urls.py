__author__ = 'jblowe'

from django.conf.urls import patterns, url
from toolbox import views

urlpatterns = patterns('',
                       url(r'^$', views.toolbox, name='toolbox'),
                       url(r'^json/?$', views.jsonrequest, name='jsonrequest'),
                       url(r'^update/?$', views.update, name='update'),
                       url(r'^(?P<appname>[\w\-]+)/?', views.tool, name='toolbox'),
                       )
