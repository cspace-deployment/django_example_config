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
from locationutils import find_items_in_cspace, setup_solr_search
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
prmz.MOVEMENTCSIDFIELD = locationConfig.get('locationhistory', 'MOVEMENTCSIDFIELD')

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

    return render(request, 'locationhistory.html', context)

def results(request):

    context = setConstants({}, prmz, request)
    context['additionalInfo'] = AdditionalInfo.objects.filter(live=True)

    if request.method == 'POST':
        prmz.MAXFACETS = 0
        context['searchValues'] = {'map-bmapper': '', 'querystring': ''}
        context['maxresults'] = prmz.MAXRESULTS
        context['displayType'] = 'list'

        # copy input form fields into context so they are preserved...
        #for i in 'gr.group lo.location ob.objects'.split(' '):
        #    if i in request.POST:
        #        context[i] = request.POST[i]

        messages = []

        #if 'group' in request.POST or 'location' in request.POST or 'objects' in request.POST:
        if request.POST['searchtype'] == 'search-group':
            context['clicked'] = 'group'
            group = request.POST['gr.group']
            if group == '':
                messages = ['A value for group title is required.']
            else:
                grouptitle, groupcsid, totalItems, list_of_objects, errormsg = find_items_in_cspace(request, 'group', urllib.quote_plus(group), prmz.MAXRESULTS)

                if groupcsid is not None and len(list_of_objects) > 0:
                    queryterms = [prmz.CSIDFIELD + ':(' + " OR ".join(list_of_objects) + ')']
                    context['searchterm'] = group
                    context = setup_solr_search(queryterms, context, prmz, request, group)
                    context['count'] = totalItems

        elif request.POST['searchtype'] == 'search-location':
            context['clicked'] = 'location'
            location = request.POST['lo.location'].strip()
            if location == '':
                messages = ['A value for storage location is required.']
            else:
                # first we find all the movement records that use this location
                queryterms = ['location_txt: "%s"' % location]
                context['searchterm'] = location
                context = setup_solr_search(queryterms, context, prmz, request, location)

                # then we find the CSIDs of the objects that have been in that location
                csids = [item['csid'] for item in context['items']]
                csids = list(set(csids))
                totalItems = len(csids)

                if totalItems > prmz.MAXRESULTS:
                    messages += ['This location housed %s objects and so is too big for location history. Maximum number of members locationhistory can handle is %s' % (totalItems, prmz.MAXRESULTS)]
                else:
                    # then we search for those objects
                    queryterms = [prmz.CSIDFIELD + ':(' + " OR ".join(csids) + ')']
                    context = setup_solr_search(queryterms, context, prmz, request, location)
                    context['count'] = totalItems

                    if totalItems > prmz.MAXRESULTS:
                        messages += ['%s objects passed through this location and so it is too big for location history. Maximum number of members locationhistory can handle is %s' % (totalItems, prmz.MAXRESULTS)]

                if 'errormsg' in context:
                    messages.append(context['errormsg'])

        elif request.POST['searchtype'] == 'search-objects':
            context['clicked'] = 'objects'
            objectnumbers = request.POST['ob.objects']
            objectnumbers = re.sub(r"[\r\n\t ]+", ' ', objectnumbers)
            objectnumbers = objectnumbers.strip()
            if objectnumbers == '':
                messages = ['One or more museum numbers is required.']
            else:
                objectnumbers_escaped = objectnumbers.replace(')', '\)').replace('(', '\(').replace('+', '\+')
                objectnumbers_escaped = objectnumbers_escaped.split(' ')
                context['searchterm'] = objectnumbers
                objectnumbers = objectnumbers.split(' ')
                if len(objectnumbers) > 0:
                    queryterms = ['objectnumber_s' + ':(' + " OR ".join(objectnumbers_escaped) + ')']
                context = setup_solr_search(queryterms, context, prmz, request, '')
                totalItems = len(context['items'])
                context['count'] = totalItems

                if totalItems > prmz.MAXRESULTS:
                    messages += ['This list of objects too big (%s) for location history. Maximum number of members locationhistory can handle is %s' % (totalItems, prmz.MAXRESULTS)]
                if 'errormsg' in context:
                    messages.append(context['errormsg'])

        if len(messages) > 0:
            context['messages'] = messages

    return render(request, 'location_results_panel.html', context)