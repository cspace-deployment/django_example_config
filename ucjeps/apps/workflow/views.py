__author__ = 'jblowe'

import re
import urllib

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

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

from common import cspace
from cspace_django_site.main import cspace_django_site

config = cspace_django_site.getConfig()
TITLE = 'Review accessions by date updated'


@login_required()
def workflow(request):
    if 'start_date' in request.GET and request.GET['start_date']:
        size_limit = 1000
        start_date = request.GET['start_date']
        try:
            end_date = request.GET['end_date']
        except:
            end_date = start_date
        if end_date == '':
            end_date = start_date
        # do search
        start_date_timestamp = start_date.strip() + "T00:00:00"
        end_date_timestamp = end_date.strip() + "T23:59:59"
        connection = cspace.connection.create_connection(config, request.user)
        search_terms = 'as=collectionspace_core:updatedAt >= TIMESTAMP "%s" AND collectionspace_core:updatedAt <= TIMESTAMP "%s"'
        #search_terms = urllib.quote_plus(search_terms % (start_date, end_date))
        search_terms = search_terms % (start_date_timestamp, end_date_timestamp)
        search_terms = search_terms.replace(' ', '%20')
        print 'cspace-services/%s?%s&pgSz=%s&wf_deleted=false' % ('collectionobjects', search_terms, size_limit)
        (url, data, statusCode,elapsedtime) = connection.make_get_request('cspace-services/%s?%s&pgSz=%s&wf_deleted=false' % ('collectionobjects', search_terms, size_limit))
        # ...collectionobjects?kw=%27orchid%27&wf_deleted=false
        results = []
        error_message = ''
        try:
            cspaceXML = fromstring(data)
            items = cspaceXML.findall('.//list-item')
            for i in items:
                outputrow = []
                csid = i.find('.//csid')
                csid = csid.text
                objectNumber = i.find('.//objectNumber')
                if objectNumber is not None:
                    objectNumber = objectNumber.text
                else:
                    objectNumber = 'No accession number'
                hostname = connection.protocol + ':' + connection.hostname
                if connection.port != '': hostname = hostname + ':' + connection.port
                link = '%s/collectionspace/ui/%s/html/cataloging.html?csid=%s' % (hostname, connection.tenant, csid)
                outputrow.append(link)
                outputrow.append(objectNumber)
                additionalfields = []
                for field in ['taxon', 'typeSpecimenKind', 'updatedAt']:
                    element = i.find('.//%s' % field)
                    element = '' if element is None else element.text
                    # extract display name if a refname... nb: this pattern might do damage in some cases!
                    element = re.sub(r"^.*\)'(.*)'$", "\\1", element)
                    additionalfields.append(element)
                outputrow.append(additionalfields)
                results.append(outputrow)
        except:
            raise
            error_message = 'Query failed.'
        return render(request, 'workflow.html',
                      {'apptitle': TITLE, 'results': results, 'start_date': start_date, 'end_date': end_date,
                       'error': error_message, 'size_limit': size_limit,
                       'labels': 'Accession Number|Taxon Name|Type Specimen Kind|Updated At'.split('|')})

    else:
        return render(request, 'workflow.html', {'apptitle': TITLE})
