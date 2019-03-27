__author__ = 'jblowe'

from django.conf.urls import url
from csvimport import views

urlpatterns = [

    url(r'^$', views.upload_file),
    url(r'uploadfile', views.upload_file, name='uploadfile'),
    # url(r'checkimagefilenames', views.checkimagefilenames, name='checkimagefilenames'),
    url(r'showqueue', views.showqueue, name='showqueue'),
    url(r'downloadresults/(?P<filename>[\w\-\.]+)$', views.downloadresults, name='downloadresults'),
    url(r'showresults/(?P<filename>[\w\-\.]+)$', views.showresults, name='showresults'),
    url(r'deletejob/(?P<jobname>[\w\-\.]+)$', views.deletejob, name='deletejob'),
    url(r'nextstep/(?P<step>[\w\-\.]+)/(?P<filename>[\w\-\.]+)$', views.nextstep, name='nextstep'),
    url(r'showcsvconfig', views.show_csv_config, name='showcsvconfig'),

]
