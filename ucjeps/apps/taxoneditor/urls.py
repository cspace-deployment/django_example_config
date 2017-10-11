__author__ = 'jblowe'

from django.conf.urls import patterns, url
from taxoneditor import views

urlpatterns = patterns('',
                       url(r'^$', views.taxoneditor, name='index'),
                       url(r'^search$', views.search, name='search'),
                       url(r'^create/?', views.create_taxon, name='create_taxon'),
                       )
