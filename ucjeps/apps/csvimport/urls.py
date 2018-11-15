__author__ = 'jblowe'

from django.conf.urls import patterns, url
from csvimport import views

urlpatterns = patterns('',
                       url(r'^/?$', views.upload_file),
                       url(r'^upload', views.upload_file, name='upload'),
                       url(r'^showcsvconfig', views.show_csv_config, name='showcsvconfig'),
                       url(r'^process', views.process_file, name='process')
                       )
