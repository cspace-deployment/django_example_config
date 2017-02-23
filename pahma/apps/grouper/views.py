__author__ = 'jblowe'

import os
import re
import time
import logging
import urllib

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, render_to_response

from common.utils import doSearch, setConstants, loginfo
from common.appconfig import loadConfiguration, loadFields, getParms
from common import cspace # we use the config file reading function
from grouputils import find_group, create_group, add2group, delete_from_group
from cspace_django_site import settings
from os import path
from .models import AdditionalInfo

config = cspace.getConfig(path.join(settings.BASE_PARENT_DIR, 'config'), 'grouper')

# read common config file
common = 'common'
prmz = loadConfiguration(common)
print 'Configuration for %s successfully read' % common

groupConfig = cspace.getConfig(path.join(settings.BASE_PARENT_DIR, 'config'), 'grouper')
prmz.FIELDDEFINITIONS = groupConfig.get('grouper', 'FIELDDEFINITIONS')

# add in the the field definitions...
prmz = loadFields(prmz.FIELDDEFINITIONS, prmz)

# override a couple parameters for this app
prmz.MAXRESULTS = int(groupConfig.get('grouper', 'MAXRESULTS'))
prmz.TITLE = groupConfig.get('grouper', 'TITLE')
prmz.NUMBERFIELD = groupConfig.get('grouper', 'NUMBERFIELD')

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
            grouptitle, groupcsid, list_of_objects = find_group(request, urllib.quote_plus(request.POST['gr.group']))
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
                    queryterms.append('%s: (' % prmz.NUMBERFIELD + " OR ".join(objectnumbers) + ')')
        context['searchValues']['querystring'] = ' OR '.join(queryterms)
        context['searchValues']['url'] = ''
        if 'submit' in request.POST:

            # do search
            loginfo(logger, 'start grouper search', context, request)
            context = doSearch(context, prmz, request)
            itemsfound = [item['accession'] for item in context['items']]
            messages = ['"%s" not found and so not included.' % accession for accession in objectnumbers if accession not in itemsfound ]
            if len(messages) > 0:
                context['messages'] = messages

        elif 'updategroup' in request.POST:
            grouptitle, groupcsid, list_of_objects = find_group(request, urllib.quote_plus(request.POST['gr.group']))
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
            messages = []
            messages += add2group(groupcsid, items2add, request)
            messages += delete_from_group(groupcsid, items2delete, request)
            # it's complicated: we can't search in Solr for the group, as we may have just created or updated it.
            # so we have to do a REST calls to find the group and its CSIDs, then we can search Solr
            # though we might still miss some... :-(
            grouptitle, groupcsid, list_of_objects = find_group(request, urllib.quote_plus(request.POST['gr.group']))
            context['searchValues']['querystring'] = '%s: (' % 'csid_s' + " OR ".join(list_of_objects) + ')'
            loginfo(logger, 'start grouper search', context, request)
            context = doSearch(context, prmz, request)
            context['messages'] = messages
        return render(request, 'grouper.html', context)

    else:
        
        return render(request, 'grouper.html', context)
