__author__ = 'jblowe'

import os
import re
import time
import urllib

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, render_to_response

from common.utils import setConstants
from common.appconfig import loadConfiguration, loadFields, getParms
from common import cspace # we use the config file reading function
from locationutils import find_group, setup_solr_search
from cspace_django_site import settings
from os import path
from .models import AdditionalInfo

config = cspace.getConfig(path.join(settings.BASE_PARENT_DIR, 'config'), 'locationhistory')

# read common config file
common = 'common'
prmz = loadConfiguration(common)
print 'Configuration for %s successfully read' % common

locationConfig = cspace.getConfig(path.join(settings.BASE_PARENT_DIR, 'config'), 'locationhistory')
prmz.FIELDDEFINITIONS = locationConfig.get('locationhistory', 'FIELDDEFINITIONS')

# add in the the field definitions...
prmz = loadFields(prmz.FIELDDEFINITIONS, prmz)

# override / add a couple parameters for this app
prmz.MAXRESULTS = int(locationConfig.get('locationhistory', 'MAXRESULTS'))
prmz.TITLE = locationConfig.get('locationhistory', 'TITLE')
prmz.NUMBERFIELD = locationConfig.get('locationhistory', 'NUMBERFIELD')
prmz.CSIDFIELD = locationConfig.get('locationhistory', 'CSIDFIELD')

print 'Configuration for %s successfully read' % 'locationhistory'

def remove_items(context):
    for item in 'locationaction items labels count'.split(' '):
        try:
            del context[item]
        except:
            pass

@login_required()
def index(request):

    context = setConstants({}, prmz, request)
    context['additionalInfo'] = AdditionalInfo.objects.filter(live=True)

    if request.method == 'POST':
        prmz.MAXFACETS = 0
        context['searchValues'] = {'map-bmapper': '', 'querystring': ''}
        context['maxresults'] = prmz.MAXRESULTS
        context['displayType'] = 'list'

        context['group'] = request.POST['gr.group']

        messages = []
        groupcsid = None
        queryterms = []

        if 'submit' in request.POST:
            # we piggyback on the "bmapper search handling" here: we don't want
            # doSearch to construct the query string for us 'cause it won't
            # do it right: we make our own below that merges the group results (if any)
            # with the list of object numbers (if any)
            if 'gr.group' in request.POST:
                group = request.POST['gr.group']
                if group == '':
                    messages = ['A value for group title (either an existing group or a potential new one) is required.']
                else:
                    grouptitle, groupcsid, totalItems, list_of_objects, errormsg = find_group(request, urllib.quote_plus(group), prmz.MAXRESULTS)

                    if groupcsid is not None and len(list_of_objects) > 0:
                        queryterms.append(prmz.CSIDFIELD + ':(' + " OR ".join(list_of_objects) + ')')
                        context = setup_solr_search(queryterms, context, prmz, request)
                        context['count'] = totalItems

                    if totalItems > prmz.MAXRESULTS:
                        messages += ['This group has %s members and so is too big for location history. Maximum number of members locationhistory can handle is %s' % (totalItems, prmz.MAXRESULTS)]
                    if errormsg is not None:
                        messages.append(errormsg)

        if len(messages) > 0:
            context['messages'] = messages
        return render(request, 'locationhistory.html', context)

    else:
        return render(request, 'locationhistory.html', context)
