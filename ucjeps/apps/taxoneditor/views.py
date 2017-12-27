__author__ = 'jblowe'

import re
import requests
import urllib
import time

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import HttpResponse
from taxon import taxon_template

from utils import termTypeDropdowns, termStatusDropdowns, taxonRankDropdowns, taxonfields, labels, formfields, numberWanted
from utils import extractTag, xName, TITLE, taxon_authority_csid, tropicos_api_key
from utils import fromstring, lookupMajorGroup

# alas, there are many ways the XML parsing functionality might be installed.
# the following code attempts to find and import the best...

from common import cspace
from cspace_django_site.main import cspace_django_site

# read common config file
from common.appconfig import loadConfiguration
prmz = loadConfiguration('common')
print 'Configuration for common successfully read'

# TODO: simplify this code: parms should be read and URLs created in a single place
config = cspace_django_site.getConfig()
tenant = config.get('cspace_services_connect', 'tenant')
hostname = config.get('cspace_services_connect', 'hostname')
port = config.get('cspace_services_connect', 'port')
protocol = config.get('cspace_services_connect', 'protocol')
cspaceserver = protocol + "://" + hostname
try:
    int(port)
    cspaceserver= cspaceserver + ':' + port
except:
    pass

@login_required()
def taxoneditor(request):

    formfield = 'determinations'
    timestamp = 'timestamp'
    sources = []
    determinations = ''
    multipleresults = []

    if request.method == 'POST':
        determinations = request.POST[formfield]
        taxa = determinations.split('\n')
        if 'source' in request.POST:
            sources = request.POST.getlist('source')
        else:
            sources = []
        # do search
        itemcount = 0
        sequence_number = 0
        for taxon in taxa:
            itemcount += 1
            # remove leading and trailing white space
            taxon = taxon.strip()
            taxon_prefix = taxon.replace('. ', '.')
            taxon_prefix = re.sub(r' +\(.*','',taxon_prefix)
            # extract just latin name (= "Genus species"
            taxon_prefix = re.sub(r'([A-Z][a-z\-]+) ([a-z\-]+).*',r'\1 \2', taxon_prefix)
            if taxon == '': continue
            results = {'CollectionSpace': [], 'GBIF': [], 'Tropicos': []}
            elapsedTimes = {'CollectionSpace': 0.0, 'GBIF': 0.0, 'Tropicos': 0.0}
            # '() NameId Family ScientificNameWithAuthors ScientificName () NameId'
            if 'CSpace' in sources:
                cspaceTime = time.time()
                connection = cspace.connection.create_connection(config, request.user)
                requestURL = 'cspace-services/taxonomyauthority/%s/items?pt=%s&wf_deleted=false&pgSz=%s' % (
                    taxon_authority_csid, urllib.quote_plus(taxon_prefix), numberWanted)
                (url, data, statusCode, elapsedTime) = connection.make_get_request(requestURL)
                if statusCode != 200 or data is None:
                    data = '<error>error %s</error>' % statusCode
                cspaceXML = fromstring(data)
                items = cspaceXML.findall('.//list-item')
                numberofitems = len(items)
                if numberofitems > numberWanted:
                    items = items[:numberWanted]
                for i in items:
                    sequence_number += 1
                    csid = i.find('.//csid')
                    csid = csid.text
                    termDisplayName = extractTag(i,'termDisplayName')
                    taxonRefname = extractTag(i,'taxon')
                    (url, taxondata, statusCode, elapsedTime) = connection.make_get_request(
                        'cspace-services/taxonomyauthority/%s/items/%s' % (taxon_authority_csid, csid))
                    print '%s cspace-services/taxonomyauthority/%s/items/%s' % (elapsedTime, taxon_authority_csid, csid)
                    taxonXML = fromstring(taxondata)
                    family = extractTag(taxonXML, 'family')
                    major_group = extractTag(taxonXML, 'taxonMajorGroup')
                    updated_at = extractTag(taxonXML, 'updatedAt')
                    #termDisplayName = extractTag(taxonXML, 'termDisplayName')
                    termName = extractTag(taxonXML, 'termName')
                    commonName = extractTag(taxonXML, 'commonName')

                    r = [sequence_number, family, major_group, termDisplayName, termName, commonName, 'CSpace', csid, updated_at]
                    r = [ ['', x] for x in r]

                    # hardcoded here for now, should eventually get these from the authentication backend
                    # but tenant is not even stored there...
                    #h ostname = 'pahma.cspace.berkeley.edu'
                    # tenant = 'pahma'
                    # link = 'http://%s/collectionspace/ui/%s/html/cataloging.html?csid=%s' % (hostname, tenant, csid)
                    results['CollectionSpace'].append(r)
                cspaceTime = time.time() - cspaceTime
                elapsedTimes['CollectionSpace'] += cspaceTime
                print '%s %s %s items %s' % (itemcount, cspaceTime, numberofitems, url)
            if 'Tropicos' in sources:
                tropicosTime = time.time()
                # do Tropicos search
                # params = urllib.urlencode({'name': taxon})
                tropicosURL = "http://services.tropicos.org/Name/Search"
                response = requests.get(tropicosURL, params={'name': taxon_prefix.replace('.','%2E'), 'pagesize':numberWanted, 'apikey':tropicos_api_key, 'format': 'json'})
                #print tropicosURL
                response.encoding = 'utf-8'
                try:
                    names2use = response.json()
                    if 'Error' in names2use[0]:
                        print 'Error from Tropicos: %s' % names2use['Error']
                        names2use = []
                except:
                    print 'could not parse returned JSON, or it was empty'
                    names2use = []
                numberofitems = len(names2use)
                if len(names2use) > numberWanted:
                    names2use = names2use[:numberWanted]
                for name in names2use:
                    sequence_number += 1
                    r = []
                    for i,fieldname in enumerate('X Family X ScientificNameWithAuthors ScientificName CommonName X NameId'.split(' ')):
                        r.append(xName(name, fieldname, i))
                    r[0] = ['id', sequence_number]
                    r[6] = ['termSource', 'Tropicos']
                    #r = {'id': sequence_number, 'family': name['Family'], 'idsource': 'Tropicos', 'id': name['NameId'],
                    #     'scientificnamewithauthors': name['ScientificNameWithAuthors'],
                    #     'scientificname': name['ScientificName']}
                    results['Tropicos'].append(r)
                tropicosTime = time.time() - tropicosTime
                elapsedTimes['Tropicos'] += tropicosTime
                print '%s %s %s items http://api.gbif.org/v1/species/search/?q=%s' % (itemcount, tropicosTime, numberofitems, urllib.quote_plus(taxon_prefix))
            if 'GBIF' in sources:
                gbifTime = time.time()
                # do GBIF search
                # params = urllib.urlencode({'name': taxon_prefix})
                response = requests.get('http://api.gbif.org/v1/species/search', params={'q': taxon_prefix})
                response.encoding = 'utf-8'

                names2use = response.json()
                names2use = names2use['results']
                numberofitems = len(names2use)
                if len(names2use) > numberWanted:
                    names2use = names2use[:numberWanted]
                for name in names2use:
                    if 'accordingTo' in name and 'NUB Generator' in name['accordingTo']:
                        continue
                    sequence_number += 1
                    # get phylum from both?!
                    r = []
                    for i,fieldname in enumerate('X family phylum scientificName canonicalName CommonName X taxonID'.split(' ')):
                        r.append(xName(name, fieldname, i))
                    r[2][1] = lookupMajorGroup(r[2][1])
                    r[0] = ['id', sequence_number]
                    r[6] = ['termSource', 'GBIF']
                    results['GBIF'].append(r)
                gbifTime = time.time() - gbifTime
                elapsedTimes['GBIF'] += gbifTime
                print '%s %s %s items http://api.gbif.org/v1/parser/name/%s' % (itemcount, gbifTime, numberofitems, urllib.quote_plus(taxon_prefix))
            multipleresults.append([taxon, taxon_prefix, results, itemcount])

    return render(request, 'taxoneditor.html', {'timestamp': timestamp, 'version': prmz.VERSION, 'fields': formfields,
                                                'labels': labels, 'multipleresults': multipleresults, 'taxa': determinations,
                                                'suggestsource': 'solr', 'sources': sources,
                                                'institution': tenant,
                                                'cspaceserver': cspaceserver,
                                                'csrecordtype': 'taxon',
                                                'apptitle': TITLE})

@login_required()
def search(request):
    pass

def load_payload(payload, request, cspace_fields):
    for field in cspace_fields:
        cspace_name = field[0]
        if cspace_name in request.POST.keys():
            payload = payload.replace('{%s}' % cspace_name, request.POST[cspace_name])

    # get rid of any unsubstituted items in the template
    payload = re.sub(r'\{.*?\}', '', payload)
    #payload = payload.replace('INSTITUTION', institution)
    return payload


@login_required()
def create_taxon(request):

    payload = load_payload(taxon_template,request,taxonfields)
    uri = 'cspace-services/%s/%s/items' % ('taxonomyauthority', taxon_authority_csid)
    #uri = 'cspace-services/%s' % 'taxonomyauthority'

    elapsedtimetotal = time.time()
    messages = {}
    # messages.append("posting to %s REST API..." % uri)
    # print payload
    # messages.append(payload)

    connection = cspace.connection.create_connection(config, request.user)
    try:
        (url, data, taxonCSID, elapsedtime) = connection.postxml(uri=uri, payload=payload, requesttype='POST')
        #(url, data, statusCode) = connection.postxml('cspace-services/%s/%s' % (service,item_csid))
        #(url, data, taxonCSID, elapsedtime) = postxml('POST', uri, http_parms.realm, http_parms.hostname, http_parms.username, http_parms.password, payload)
    # elapsedtimetotal += elapsedtime
    except:
        messages['error'] = '%s REST API post failed...' % uri
        return messages

    messages['item'] = request.POST['item']
    messages['csid'] = taxonCSID
    messages['elapsedtime'] = elapsedtime
    return render(request, 'taxon_save_result.html', messages)
