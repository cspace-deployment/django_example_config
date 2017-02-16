__author__ = 'jblowe'

import os
import re
import time
import logging

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, render_to_response

from common.utils import doSearch, setConstants, loginfo
from common.appconfig import loadConfiguration, loadFields, getParms
from common import cspace # we use the config file reading function
from grouputils import find_group, create_group, add2group
from cspace_django_site import settings
from os import path
from .models import AdditionalInfo

config = cspace.getConfig(path.join(settings.BASE_PARENT_DIR, 'config'), 'grouper')

# read common config file
common = 'common'
prmz = loadConfiguration(common)
print 'Configuration for %s successfully read' % common

searchConfig = cspace.getConfig(path.join(settings.BASE_PARENT_DIR, 'config'), 'grouper')
prmz.FIELDDEFINITIONS = searchConfig.get('grouper', 'FIELDDEFINITIONS')

# add in the the field definitions...
prmz = loadFields(prmz.FIELDDEFINITIONS, prmz)

# override a couple parameters for this app
prmz.MAXRESULTS = int(searchConfig.get('grouper', 'MAXRESULTS'))
prmz.TITLE = searchConfig.get('grouper', 'TITLE')

print 'Configuration for %s successfully read' % 'grouper'

# Get an instance of a logger, log some startup info
logger = logging.getLogger(__name__)
logger.info('%s :: %s :: %s' % ('grouper startup', '-', '%s | %s' % (prmz.SOLRSERVER, prmz.IMAGESERVER)))


@login_required()
def index(request):

    context = setConstants({}, prmz, request)
    context['additionalInfo'] = AdditionalInfo.objects.filter(live=True)

    if request.method == 'POST':
        prmz.MAXFACETS = 0

        queryterms = []
        # we piggyback on the "bmapper search handling" here: we don't want
        # doSearch to construct the query string for us 'cause it won't
        # do it right: we make our own below that merges the group results (if any)
        # with the list of object numbers (if any)
        context['searchValues'] = {'map-bmapper': '', 'querystring': ''}
        context['maxresults'] = prmz.MAXRESULTS
        context['displayType'] = 'list'
        if 'gr.group' in request.POST:
            context['group'] = request.POST['gr.group']
            #context['searchValues']['grouptitle'] =request.POST['gr.group']
            grouptitle, groupcsid, list_of_objects = find_group(request, request.POST['gr.group'])
            if groupcsid is not None:
                queryterms.append('csid_s:(' + " OR ".join(list_of_objects) + ')')
                context['groupaction'] = 'Update Group'
            else:
                context['groupaction'] = 'Create Group'
        if 'objects' in request.POST:
            objectnumbers = request.POST['objects'].strip()
            if objectnumbers == '':
                pass
            else:
                context['objects'] = objectnumbers
                objectnumbers = objectnumbers.split(' ')
                if len(objectnumbers) > 0:
                    objectnumberfield = "accessionnumber_s"
                    queryterms.append('%s: (' %objectnumberfield + " OR ".join(objectnumbers) + ')')
        context['searchValues']['querystring'] = ' OR '.join(queryterms)
        context['searchValues']['url'] = ''
        if 'submit' in request.POST:

            # do search
            loginfo(logger, 'start grouper search', context, request)
            context = doSearch(context, prmz, request)

        elif 'updategroup' in request.POST:
            grouptitle, groupcsid, list_of_objects = find_group(request, request.POST['gr.group'])
            if groupcsid is None:
                groupcsid = create_group(request.POST['gr.group'], request)
            items2add = []
            items2delete = []
            items_included = []
            for item in request.POST:
                if "item-" in item:
                    items_included.append(request.POST[item])
                    if request.POST[item] in list_of_objects:
                        pass
                    else:
                        items2add.append(request.POST[item])
            for item in list_of_objects:
                if item in items_included:
                    pass
                else:
                    items2delete.append(item)
            add2group(groupcsid, items2add, request)
            grouptitle, groupcsid, list_of_objects = find_group(request, request.POST['gr.group'])
            context['searchValues']['querystring'] = '%s: (' % 'csid_s' + " OR ".join(list_of_objects) + ')'
            loginfo(logger, 'start grouper search', context, request)
            context = doSearch(context, prmz, request)
        return render(request, 'grouper.html', context)

    else:
        
        return render(request, 'grouper.html', context)
