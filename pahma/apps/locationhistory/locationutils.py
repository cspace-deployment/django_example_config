import time
import logging
import urllib2
from cspace_django_site.main import cspace_django_site
from common import cspace
import solr
from common.utils import loginfo


# alas, there are many ways the XML parsing functionality might be installed.
# the following code attempts to find and import the best...
try:
    from xml.etree.ElementTree import tostring, parse, Element, fromstring

    print("running with xml.etree.ElementTree")
except ImportError:
    try:
        from lxml import etree

        print("running with lxml.etree")
    except ImportError:
        try:
            # normal cElementTree install
            import cElementTree as etree

            print("running with cElementTree")
        except ImportError:
            try:
                # normal ElementTree install
                import elementtree.ElementTree as etree

                print("running with ElementTree")
            except ImportError:
                print("Failed to import ElementTree from any known place")

# global variables (at least to this module...)
config = cspace_django_site.getConfig()

# Get an instance of a logger, log some startup info
logger = logging.getLogger(__name__)
logger.info('%s :: %s :: %s' % ('location history startup', '-', '%s | %s' % ('', '')))


def getfromCSpace(uri, request):
    connection = cspace.connection.create_connection(config, request.user)
    url = "cspace-services/" + uri
    return connection.make_get_request(url)


def find_group(request, grouptitle, pgSz):

    # TIMESTAMP = time.strftime("%b %d %Y %H:%M:%S", time.localtime())

    asquery = '%s?as=%s_common%%3Atitle%%3D%%27%s%%27&wf_deleted=false&pgSz=%s' % ('groups', 'groups', grouptitle, pgSz)

    # Make authenticated connection to cspace server...
    (groupurl, grouprecord, dummy, elapsedtime) = getfromCSpace(asquery, request)
    if grouprecord is None:
        return(None, None, 0, [], 'Error: the search for group \'%s.\' failed.' % grouptitle)
    grouprecordtree = fromstring(grouprecord)
    groupcsid = grouprecordtree.find('.//csid')
    if groupcsid is None:
        return(None, None, 0, [], None)
    groupcsid = groupcsid.text

    uri = 'collectionobjects?rtObj=%s&pgSz=%s' % (groupcsid, pgSz)
    try:
        (groupurl, groupmembers, dummy, elapsedtime) = getfromCSpace(uri, request)
        groupmembers = fromstring(groupmembers)
        totalItems = groupmembers.find('.//totalItems')
        totalItems = int(totalItems.text)
        objectcsids = [e.text for e in groupmembers.findall('.//csid')]
    except urllib2.HTTPError, e:
        return (None, None, 0, [], 'Error: we could not make list of group members')

    return (grouptitle, groupcsid, totalItems, objectcsids, None)


def setup_solr_search(queryterms, context, prmz, request):
    context['searchValues']['querystring'] = ' OR '.join(queryterms)
    context['searchValues']['url'] = ''
    context['searchValues']['maxresults'] = prmz.MAXRESULTS
    loginfo(logger, 'start location history search', context, request)
    return do_location_search(context, prmz, queryterms)


def do_location_search(context, prmz, querystring):
    elapsedtime = time.time()
    solr_server = 'http://localhost:8983/solr'
    solr_core = 'pahma-locations'
    solrfl = 'crate_s csid_s id location_s locationdate_dt objectname_s objectcount_s objectumber_s sortableobjectnumber_s storagelocation_s computedcrate_s'.replace(' ',',')

    # print 'Solr query: %s' % querystring
    try:
        startpage = context['maxresults'] * (context['start'] - 1)
    except:
        startpage = 0
        context['start'] = 1

    # create a connection to a solr server
    s = solr.SolrConnection(url='%s/%s' % (solr_server, solr_core))

    print 'query: %s' % querystring
    try:
        solrtime = time.time()
        response = s.query(querystring, facet='true', fq={}, fields=solrfl,
                           rows=context['maxresults'], facet_limit=prmz.MAXFACETS, sort=context['sortkey'],
                           facet_mincount=1, start=startpage)
        print 'Solr search succeeded, %s results, %s rows requested starting at %s; %8.2f seconds.' % (
            response.numFound, context['maxresults'], startpage, time.time() - solrtime)
    # except:
    except Exception as inst:
        # raise
        print 'Solr search failed: %s' % str(inst)
        context['errormsg'] = 'Solr4 query failed'
        return context

    results = []
    objects = {}
    locations = {}
    for i,r in enumerate(response.results):
        csid = r['csid_s']
        if csid in objects:
            pass
        else:
            locations[csid] = []
            objects[csid] = {'csid': r['csid_s'], 'sortkey': r['sortableobjectnumber_s'], 'counter': i+1, 'otherfields': []}
            for cell in 'objectumber_s objectname_s objectcount_s'.split(' '):
                if cell in r:
                    objects[csid]['otherfields'].append({'name' :cell, 'value': r[cell]})
                else:
                    objects[csid]['otherfields'].append({'name': cell, 'value': ''})
        output_list = []
        for cell in 'locationdate_dt location_s crate_s'.split(' '):
            if cell in r:
                output_list.append(str(r[cell]))
            else:
                output_list.append(" - ")
        locations[csid].append(' :: '.join(output_list))

    for csid in objects.keys():
        row = objects[csid]
        row['otherfields'].append({'name' :'locations', 'value': sorted(locations[csid], reverse=True), 'multi': 2})
        # for cell in 'objectumber_s location_s crate_s locationdate_dt objectcount_s storagelocation_s computedcrate_s'.split(' '):
        results.append(row)

    context['labels'] = 'Musuem Number,Object Name,Count,Locations (date :: location :: crate)'.split(',')
    context['items'] = results
    context['querystring'] = querystring
    context['core'] = solr_core
    context['time'] = '%8.3f' % (time.time() - elapsedtime)
    return context
