__author__ = 'jblowe'

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, HttpResponse
import json
from django.conf import settings
import os
import time
import ConfigParser

from cspace_django_site.main import cspace_django_site
from common import cspace, appconfig
from common.utils import devicetype
from cswaMain import main
from cswaUtils import downloadCsv

from cswaConstants import BASE_DIR

config = cspace_django_site.getConfig()
hostname = cspace.getConfigOptionWithSection(config,
                                             cspace.CONFIGSECTION_AUTHN_CONNECT,
                                             cspace.CSPACE_HOSTNAME_PROPERTY)

TITLE = 'Tools Available'


def index(request):
    context = {}
    context['version'] = appconfig.getversion()
    context['labels'] = 'name file'.split(' ')
    context['apptitle'] = TITLE
    context['hostname'] = hostname
    context['device'] = devicetype(request)
    context['timestamp'] = time.strftime("%b %d %Y %H:%M:%S", time.localtime())
    context['html'] = main(request, '')
    context['extra_nav'] = {'href': './', 'id': 'switchtool', 'name': 'Switch Tool'}
    return render(request, 'index.html', context)


def toolbox(request, action):
    context = {}
    context['version'] = appconfig.getversion()
    context['labels'] = 'name file'.split(' ')

    # the biggest problem with this approach is that the config file for the tool
    # is re-read every time the tool is started by a user...
    # on the other hand, it may provide a means for real time updates of configuration...
    webappconfig = ConfigParser.RawConfigParser()
    webappconfig.read(os.path.join(BASE_DIR, action + '.cfg'))
    context['apptitle'] = webappconfig.get('info', 'apptitle')
    context['hostname'] = hostname
    context['device'] = devicetype(request)
    context['timestamp'] = time.strftime("%b %d %Y %H:%M:%S", time.localtime())
    context['html'] = main(request, action)


    if (action == 'packinglist' or action == 'governmentholdings'):
        # html += starthtml(form, config)
        form = {}
        for r in request.POST.keys():
            form[r] = request.POST[r]
        if 'action' in form and form['action'] == 'Download as CSV':
            response = downloadCsv(form, webappconfig)
            # elapsedtime = time.time() - elapsedtime
            #writeInfo2log('end', form, config, elapsedtime)
            # html += endhtml(form, config, elapsedtime)
            return response

    context['extra_nav'] = {'href': './', 'id': 'switchtool', 'name': 'Switch Tool'}
    return render(request, 'index.html', context)


