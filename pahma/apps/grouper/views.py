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
from grouputils import find_group, create_group, add2group, delete_from_group, setup_solr_search
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
        messages = []
        groupcsid = None
        if 'gr.group' in request.POST:
            if request.POST['gr.group'] == '':
                messages = ['A value for group title (either an existing group or a potential new one) is required.']
            else:
                context['group'] = request.POST['gr.group']
                #context['searchValues']['grouptitle'] =request.POST['gr.group']
                grouptitle, groupcsid, list_of_objects = find_group(request, urllib.quote_plus(request.POST['gr.group']))
                if len(list_of_objects) > prmz.MAXRESULTS:
                    messages += ['This group has %s members and so is too big for Grouper. Maximum number of members is %s' % (len(list_of_objects), prmz.MAXRESULTS)]
                elif groupcsid is not None:
                    queryterms.append('csid_s:(' + " OR ".join(list_of_objects) + ')')
                    context['groupaction'] = 'Update Group'
                else:
                    context['groupaction'] = 'Create Group'
        if 'objects' in request.POST:
            objectnumbers = request.POST['objects'].strip()
            objectnumbers = re.sub(r"[\r\n ]+", ' ', objectnumbers)
            if objectnumbers == '':
                pass
            else:
                context['objects'] = objectnumbers
                objectnumbers = objectnumbers.split(' ')
                if len(objectnumbers) > 0:
                    queryterms.append('%s: (' % prmz.NUMBERFIELD + " OR ".join(objectnumbers) + ')')

        if 'submit' in request.POST:
            context = setup_solr_search(queryterms, context, prmz, request)
            if context['count'] > prmz.MAXRESULTS:
                messages += ['This group is too big for Grouper. maximum number of members is %s' % prmz.MAXRESULTS]
            elif 'items' in context:
                object_numbers_found = [item['accession'] for item in context['items']]
                obj2csid = [[item['csid'], item['accession']] for item in context['items'] if item['accession'] in objectnumbers]
                # if we are dealing with a group that already exists, we need to avoid inserting duplicates
                messages += ['"%s" not found and so not included.' % accession for accession in objectnumbers if accession not in object_numbers_found ]
                if groupcsid is not None:
                    messages += ['"%s" already in member list and so not duplicated.' % item[1] for item in obj2csid if item[0] in list_of_objects]
                if prmz.MAXRESULTS < context['count']:
                    messages += ['Only %s items of %s are displayed below and can be managed.' % (prmz.MAXRESULTS, context['count'])]
            else:
                messages += ['problem with Solr query: %s' % context['searchValues']['querystring'] ]

        elif 'updategroup' in request.POST:
            grouptitle, groupcsid, list_of_objects = find_group(request, urllib.quote_plus(request.POST['gr.group']))

            # it's complicated: we can't search in Solr for the group, as we may have just created or updated it.
            # so we have to do a REST calls to find the group and its CSIDs, then we can search Solr
            # though we might still miss some... :-(
            queryterms = ['%s: (' % 'csid_s' + " OR ".join(list_of_objects) + ')']
            context = setup_solr_search(queryterms, context, prmz, request)
            if prmz.MAXRESULTS < len(context['items']):
                messages += ['Only %s items of %s are displayed below.' % (prmz.MAXRESULTS, context['items'])]

            if groupcsid is None:
                groupcsid = create_group(request.POST['gr.group'], request)
            items2add = []
            items2delete = []
            items_ignored = []
            items_included = []
            for item in request.POST:
                if "item-" in item:
                    items_included.append(request.POST[item])
                    if request.POST[item] in list_of_objects:
                        pass
                    else:
                        items2add.append(request.POST[item])
            object_numbers_found = [item['csid'] for item in context['items']]
            for i, item in enumerate(object_numbers_found):
                if item in items_included:
                    pass
                else:
                    items2delete.append(item)

            messages += add2group(groupcsid, items2add, request)
            messages += delete_from_group(groupcsid, items2delete, request)
            grouptitle, groupcsid, list_of_objects = find_group(request, urllib.quote_plus(request.POST['gr.group']))
            if len(items_ignored) > 0 : messages += ['%s items in group untouched.' % len(items_ignored)]

            queryterms = [ '%s: (' % 'csid_s' + " OR ".join(list_of_objects) + ')' ]
            context = setup_solr_search(queryterms, context, prmz, request)

        if len(messages) > 0:
            context['messages'] = messages
        return render(request, 'grouper.html', context)

    else:
        
        return render(request, 'grouper.html', context)
