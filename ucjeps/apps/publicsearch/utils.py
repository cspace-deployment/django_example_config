# -*- coding: UTF-8 -*-

import re
import time, datetime
import csv
import solr
import cgi
import logging
from os import path

from django.http import HttpResponse, HttpResponseRedirect
from cspace_django_site.main import cspace_django_site

# global variables (at least to this module...)

from appconfig import PARMS, MAXMARKERS, MAXRESULTS, MAXLONGRESULTS, MAXFACETS, IMAGESERVER, BMAPPERSERVER, BMAPPERDIR
from appconfig import BMAPPERURL, BMAPPERCONFIGFILE, SOLRSERVER, SOLRCORE, LOCALDIR, DROPDOWNS, SEARCH_QUALIFIERS, TITLE

SolrIsUp = True
FACETS = {}


# Get an instance of a logger, log some startup info
logger = logging.getLogger(__name__)
logger.info('%s :: %s :: %s' % ('portal startup', '-', '%s | %s | %s' % (SOLRSERVER, IMAGESERVER, BMAPPERSERVER)))

def loginfo(infotype, context, request):
    logdata = ''
    #user = getattr(request, 'user', None)
    if request.user and not request.user.is_anonymous():
        username = request.user.username
    else:
        username = '-'
    if 'count' in context:
        count = context['count']
    else:
        count = '-'
    if 'querystring' in context:
        logdata = context['querystring']
    if 'url' in context:
        logdata += ' :: %s' % context['url']
    logger.info('%s :: %s :: %s :: %s' % (infotype, count, username, logdata))


def getfromXML(element,xpath):
    result = element.find(xpath)
    if result is None: return ''
    result = '' if result.text is None else result.text
    result = re.sub(r"^.*\)'(.*)'$", "\\1", result)
    return result


def deURN(urn):
    #find identifier in URN
    m = re.search("\'(.*)\'$", urn)
    if m is not None:
        # strip out single quotes
        return m.group(0)[1:len(m.group(0)) - 1]


def getfields(fieldset):
    # for solr faceting
    if fieldset == 'bmapperheader':
        return ["Institution Code",
                "Catalog Number",
                "Scientific Name",
                "Collector",
                "Collector Num Prefix",
                "Collector Num",
                "Collector Num Suffix",
                "early J date",
                "late J date",
                "Date Collected",
                "County",
                "Elevation",
                "Locality",
                "Datum",
                "Latitude",
                "Longitude"]
    elif fieldset == 'bmapperdata':
        return ["na", "accession", "determination", "collector", "na", "collectionnumber", "na", "collectiondate",
                "", "", "county", "elevation", "locality", "L1", "L2", "datum"]
    elif fieldset == 'csvdata':
        return ["ucjeps", "accession", "determination", "collector", "", "collectionnumber", "", "collectiondate",
                "", "", "county", "elevation", "locality", "datum", "L1", "L2"]
    elif fieldset == 'facetfields':
        return ['determination_s', 'majorgroup_s', 'collector_ss', 'collcounty_s', 'collstate_s', 'collcountry_s']


def getfacets(response):
    #facets = response.get('facet_counts').get('facet_fields')
    facets = response.facet_counts
    facets = facets['facet_fields']
    _facets = {}
    for key, values in facets.items():
        _v = []
        for k, v in values.items():
            _v.append((k, v))
        _facets[key] = sorted(_v, key=lambda (a, b): b, reverse=True)
    return _facets



def setDisplayType(requestObject):
    if 'displayType' in requestObject:
        displayType = requestObject['displayType']
    elif 'search-list' in requestObject:
        displayType = 'list'
    elif 'search-full' in requestObject:
        displayType = 'full'
    elif 'search-grid' in requestObject:
        displayType = 'grid'
    else:
        displayType = 'list'

    return displayType


def setConstants(context):
    if not SolrIsUp: context['errormsg'] = 'Solr is down!'
    context['title'] = TITLE
    context['imageserver'] = IMAGESERVER
    context['dropdowns'] = FACETS
    context['timestamp'] = time.strftime("%b %d %Y %H:%M:%S", time.localtime())
    context['qualifiers'] = SEARCH_QUALIFIERS
    context['resultoptions'] = [100, 500, 1000, 2000, 10000]

    context['displayTypes'] = (
        ('list', 'List'),
        ('full', 'Full'),
        ('grid', 'Grid'),
    )

    # copy over form values to context if they exist
    try:
        requestObject = context['searchValues']

        context['displayType'] = setDisplayType(requestObject)
        if 'url' in requestObject: context['url'] = requestObject['url']
        if 'querystring' in requestObject: context['querystring'] = requestObject['querystring']
        if 'core' in requestObject: context['core'] = requestObject['core']
        if 'maxresults' in requestObject: context['maxresults'] = int(requestObject['maxresults'])

        if 'maxfacets' in requestObject:
            context['maxfacets'] = int(requestObject['maxfacets'])
        else:
            context['maxfacets'] = MAXFACETS

    except:
        print "no searchValues set"
        context['displayType'] = setDisplayType({})
        context['url'] = ''
        context['querystring'] = ''
        context['core'] = SOLRCORE
        context['maxresults'] = MAXRESULTS

    return context

def recodevarname(p):
    if PARMS[p][4] == 'ss':
        return PARMS[p][3].replace('_txt', '_ss')
    else:
        return PARMS[p][3].replace('_txt', '_s')

def doSearch(solr_server, solr_core, context):
    elapsedtime = time.time()
    context = setConstants(context)
    requestObject = context['searchValues']

    # create a connection to a solr server
    s = solr.SolrConnection(url='%s/%s' % (solr_server, solr_core))
    queryterms = []
    urlterms = []
    facetfields = getfields('facetfields')
    if 'map-google' in requestObject or 'csv' in requestObject or 'map-bmapper' in requestObject:
        querystring = requestObject['querystring']
        url = requestObject['url']
        # Did the user request the full set?
        if 'select-item' in requestObject:
            context['maxresults'] = min(requestObject['count'], MAXRESULTS)
            context['start'] = 1
    else:
        for p in requestObject:
            if p in ['csrfmiddlewaretoken', 'displayType', 'resultsOnly', 'maxresults', 'url', 'querystring', 'pane',
                     'pixonly', 'locsonly', 'typesonly', 'cultivated', 'acceptterms']: continue
            if '_qualifier' in p: continue
            if 'select-' in p: continue # skip select control for map markers
            if not p in requestObject: continue
            if not requestObject[p]: continue
            if 'item-' in p: continue
            searchTerm = requestObject[p]
            terms = searchTerm.split(' OR ')
            ORs = []
            for t in terms:
                t = t.strip()
                if t == 'Null':
                    t = '[* TO *]'
                    index = '-' + PARMS[p][3]
                else:
                    if p in DROPDOWNS:
                        # if it's a value in a dropdown, it must always be an "exact search"
                        t = '"' + t + '"'
                        index = recodevarname(p)
                    elif p + '_qualifier' in requestObject:
                        # print 'qualifier:',requestObject[p+'_qualifier']
                        qualifier = requestObject[p + '_qualifier']
                        if qualifier == 'exact':
                            index = recodevarname(p)
                            t = '"' + t + '"'
                        elif qualifier == 'phrase':
                            index = PARMS[p][3]
                            t = '"' + t + '"'
                        elif qualifier == 'keyword':
                            t = t.split(' ')
                            t = ' +'.join(t)
                            t = '(+' + t + ')'
                            t = t.replace('+-', '-') # remove the plus if user entered a minus
                            index = PARMS[p][3]
                    else:
                        t = t.split(' ')
                        t = ' +'.join(t)
                        t = '(+' + t + ')'
                        t = t.replace('+-', '-') # remove the plus if user entered a minus
                        index = PARMS[p][3]
                if t == 'OR': t = '"OR"'
                if t == 'AND': t = '"AND"'
                ORs.append('%s:%s' % (index, t))
            searchTerm = ' OR '.join(ORs)
            if ' ' in searchTerm and not '[* TO *]' in searchTerm: searchTerm = ' (' + searchTerm + ') '
            queryterms.append(searchTerm)
            urlterms.append('%s=%s' % (p, cgi.escape(requestObject[p])))
        querystring = ' AND '.join(queryterms)
        print querystring

        if urlterms != []:
            urlterms.append('displayType=%s' % context['displayType'])
            urlterms.append('maxresults=%s' % requestObject['maxresults'])
        url = '&'.join(urlterms)

    try:
        pixonly = requestObject['pixonly']
        querystring += " AND %s:[* TO *]" % PARMS['blobs'][3]
        url += '&pixonly=True'
    except:
        pixonly = None

    try:
        locsonly = requestObject['locsonly']
        querystring += " AND %s:[* TO *]" % PARMS['L1'][3]
        url += '&locsonly=True'
    except:
        locsonly = None

    try:
        typesonly = requestObject['typesonly']
        querystring += " AND %s:[* TO *]" % PARMS['typeassertions'][3]
        url += '&typesonly=True'
    except:
        typesonly = None

    try:
        cultivated = requestObject['cultivated']
        querystring += " AND %s:(+true)" % PARMS['cultivated'][3]
        url += '&cultivated=True'
    except:
        cultivated = None

    try:
        response = s.query(querystring, facet='true', facet_field=facetfields, fq={},
                           rows=context['maxresults'], facet_limit=MAXFACETS,
                           facet_mincount=1)
    except:
        context['errormsg'] = 'Solr4 query failed'
        return context

    facetflds = getfacets(response)
    results = response.results

    context['items'] = []
    for i, listItem in enumerate(results):
        item = {}
        item['counter'] = i
        for p in PARMS:
            try:
                # make all arrays into strings for display
                if type(listItem[PARMS[p][3]]) == type([]):
                    item[p] = ';'.join(listItem[PARMS[p][3]])
                else:
                    item[p] = listItem[PARMS[p][3]]

                # handle dates (convert them to collatable strings)
                if isinstance(item[p], datetime.date):
                    try:
                        #item[p] = item[p].toordinal()
                        item[p] = item[p].isoformat().replace('T00:00:00+00:00', '')
                    except:
                        print 'date problem: ', item[p]
            except:
                #raise
                pass

        # the following multivalue fields need to be split
        for fld in 'previousdeterminations,associatedtaxa,typeassertions,othernumber,collector,otherlocalities,comments'.split(','):
            if fld in item.keys():
                item[fld] = item[fld].split(';')

        # blobs are handled specially
        if 'blobs' in item.keys():
                item['blobs'] = item['blobs'].split(';')
        context['items'].append(item)

    if context['displayType'] in ['full', 'grid'] and response._numFound > MAXLONGRESULTS:
        context['recordlimit'] = '(limited to %s for long display)' % MAXLONGRESULTS
        context['items'] = context['items'][:MAXLONGRESULTS]
    if context['displayType'] == 'list' and response._numFound > context['maxresults']:
        context['recordlimit'] = '(display limited to %s)' % context['maxresults']

    #print 'items',len(context['items'])
    context['count'] = response._numFound
    m = {}
    context['labels'] = {}
    for p in PARMS:
        m[recodevarname(p)] = p
        context['labels'][p] = PARMS[p][0]
    context['fields'] = [m[f] for f in facetfields]
    context['facetflds'] = [[m[f], facetflds[f]] for f in facetfields]
    context['range'] = range(len(facetfields))
    context['pixonly'] = pixonly
    context['locsonly'] = locsonly
    context['typesonly'] = typesonly
    context['cultivated'] = cultivated
    try:
        context['pane'] = requestObject['pane']
    except:
        context['pane'] = '0'
    try:
        context['resultsOnly'] = requestObject['resultsOnly']
    except:
        pass

    context['url'] = url
    context['querystring'] = querystring
    context['core'] = solr_core
    context['time'] = '%8.3f' % (time.time() - elapsedtime)
    return context

# on startup, do a query to get options values for forms...
print 'Starting initialization'
context = {'displayType': 'list', 'maxresults': 0,
           'searchValues': {'csv': 'true', 'querystring': '*:*', 'url': '', 'maxfacets': 1000, 'count': 0}}
context = doSearch(SOLRSERVER, SOLRCORE, context)
#print 'solr facet search time: %s' % context['time']

start = time.time()
if 'errormsg' in context:
    solrIsUp = False
    print 'Initial solr search failed. Concluding that Solr is down or unreachable... Will not be trying again! Please fix and restart!'
else:
    for facet in context['facetflds']:
        print 'facet',facet[0],len(facet[1])
        if facet[0] in DROPDOWNS:
            FACETS[facet[0]] = sorted(facet[1])
        # if the facet is not in a dropdown, save the memory for something better
        else:
            FACETS[facet[0]] = []
print 'Initialization complete: %s' % (time.time() - start)

