__author__ = 'jblowe'

import re
import requests
import urllib
import time

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import HttpResponse
from taxon import taxon_template

from uploadmedia.cswaExtras import postxml, relationsPayload, getConfig, getCSID
from utils import termTypeDropdowns, termStatusDropdowns, taxonRankDropdowns, taxonfields, labels, formfields, numberWanted
from utils import extractTag, xName, TITLE, taxon_authority_csid, tropicos_api_key
from utils import fromstring

# alas, there are many ways the XML parsing functionality might be installed.
# the following code attempts to find and import the best...

from common import cspace
from cspace_django_site.main import cspace_django_site

config = cspace_django_site.getConfig()

@login_required()
def taxoneditor(request):

    formfield = 'determinations'
    timestamp = 'timestamp'
    version = 'version'
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
        multipleresults = []
        itemcount = 0
        sequence_number = 0
        for taxon in taxa:
            itemcount += 1
            taxon = taxon.strip()
            if taxon == '': continue
            results = {'CollectionSpace': [], 'GBIF': [], 'Tropicos': []}
            elapsedTimes = {'CollectionSpace': 0.0, 'GBIF': 0.0, 'Tropicos': 0.0}
            # '() NameId Family ScientificNameWithAuthors ScientificName () NameId'
            if 'CSpace' in sources:
                cspaceTime = time.time()
                connection = cspace.connection.create_connection(config, request.user)
                print 'cspace-services/taxonomyauthority/%s/items?pt=%s&wf_deleted=false&pgSz=%s' % (
                    taxon_authority_csid, urllib.quote_plus(taxon), numberWanted)
                (url, data, statusCode, elapsedTime) = connection.make_get_request(
                    'cspace-services/taxonomyauthority/%s/items?pt=%s&wf_deleted=false&pgSz=%s' % (
                        taxon_authority_csid, urllib.quote_plus(taxon), numberWanted))
                # 'cspace-services/%s?taxon=%s&wf_deleted=false' % ('taxon', taxon))
                # ...collectionobjects?taxon=%27orchid%27&wf_deleted=false
                cspaceXML = fromstring(data)
                items = cspaceXML.findall('.//list-item')
                numberofitems = len(items)
                for i in items:
                    sequence_number += 1
                    if sequence_number > numberWanted: break
                    csid = i.find('.//csid')
                    csid = csid.text
                    termDisplayName = extractTag(i,'termDisplayName')
                    taxonRefname = extractTag(i,'taxon')
                    (url, taxondata, statusCode, elapsedTime) = connection.make_get_request(
                        'cspace-services/taxonomyauthority/%s/items/%s' % (taxon_authority_csid, csid))
                    print '%s cspace-services/taxonomyauthority/%s/items/%s' % (elapsedTime, taxon_authority_csid, csid)
                    taxonXML = fromstring(taxondata)
                    family = extractTag(taxonXML, 'family')
                    #termDisplayName = extractTag(taxonXML, 'termDisplayName')
                    termName = extractTag(taxonXML, 'termName')
                    commonName = extractTag(taxonXML, 'commonName')

                    r = [sequence_number, family, '', termDisplayName, termName, commonName, 'CSpace', csid]
                    r = [ ['', x] for x in r]

                    # hardcoded here for now, should eventually get these from the authentication backend
                    # but tenant is not even stored there...
                    #h ostname = 'pahma.cspace.berkeley.edu'
                    # tenant = 'pahma'
                    # link = 'http://%s/collectionspace/ui/%s/html/cataloging.html?csid=%s' % (hostname, tenant, csid)
                    results['CollectionSpace'].append(r)
                elapsedTimes['CollectionSpace'] += time.time() - cspaceTime
            if 'Tropicos' in sources:
                tropicosTime = time.time()
                # do Tropicos search
                # params = urllib.urlencode({'name': taxon})
                tropicosURL = "http://services.tropicos.org/Name/Search"
                response = requests.get(tropicosURL, params={'name': taxon.replace('.','%2E'), 'pagesize':numberWanted, 'apikey':tropicos_api_key, 'format': 'json'})
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
                print '%s %s http://api.gbif.org/v1/parser/name/%s' % (itemcount, tropicosTime, urllib.quote_plus(taxon))
            if 'GBIF' in sources:
                gbifTime = time.time()
                # do Tropicos search
                # params = urllib.urlencode({'name': taxon})
                response = requests.get('http://api.gbif.org/v1/species/search', params={'q': taxon})
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
                    for i,fieldname in enumerate('X family family scientificName canonicalName CommonName X taxonID'.split(' ')):
                        r.append(xName(name, fieldname, i))
                    r[0] = ['id', sequence_number]
                    r[6] = ['termSource', 'GBIF']
                    results['GBIF'].append(r)
                gbifTime = time.time() - gbifTime
                elapsedTimes['GBIF'] += gbifTime
                print '%s %s http://api.gbif.org/v1/parser/name/%s' % (itemcount, gbifTime, urllib.quote_plus(taxon))
            multipleresults.append([taxon, results, itemcount])

    return render(request, 'taxoneditor.html', {'timestamp': timestamp, 'version': version, 'fields': formfields,
                                                'labels': labels, 'multipleresults': multipleresults, 'taxa': determinations,
                                                'suggestsource': 'solr', 'sources': sources,
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
