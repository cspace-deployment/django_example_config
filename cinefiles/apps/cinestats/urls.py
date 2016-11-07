from django.conf.urls import patterns, url

from cinestats import views

urlpatterns = patterns('',
   url(r'^$', views.index, name='index')
)
