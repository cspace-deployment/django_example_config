__author__ = 'jblowe, rjaffe'
# Calls Public Search web app. 

import re
import time
from django.shortcuts import render, render_to_response, redirect
import urllib
import urllib2
from cspace_django_site.main import cspace_django_site
from eloanutils import get_entity, build_solr_query, getInstitutionCodefromDisplayName, getShortIdfromRefName
from publicsearch.utils import getfromXML


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

from appconfig import SOLRSERVER, SOLRCORE, SOLRQUERYPARAM, PARMS

# CONSTANTS
SEARCHRESULTS = {}
TITLE = 'E-loan'


def eloan(request):
    """

    :param request:
    :return:
    """
    if 'kw' in request.GET and request.GET['kw']:

        TIMESTAMP = time.strftime("%b %d %Y %H:%M:%S", time.localtime())

        #if 'kw' conforms to the UCJEPS naming convention, continue. Else send error "E-loan numbers begin..."
        if re.match(r"^.+E[0-9]+$", request.GET['kw']) is not None:
            eloanNum = urllib.quote_plus(request.GET['kw'])
            eloanNum = str(eloanNum)
        else:
            errMsg = 'Error: E-loan numbers begin with a collection code, followed by a capital E and only digits after that. You entered: '+request.GET['kw']
            return render(request, 'eloan.html',
                          {'results': errMsg, 'displayType': 'error', 'title': TITLE, 'timestamp': TIMESTAMP }
            )

        if 'recType' in request.GET and request.GET['recType']:

            recType = urllib.quote_plus(request.GET['recType'])
            recType = str(recType)

        # Record type hard-coded for now in eloan.html. Generalize?
        # This else clause in not really needed.
        else:
            try:
                recType = 'loansout'
            except urllib2.HTTPError, e:
                print 'Error1'
                return

        #################################################################
        #  GET E-LOAN INFORMATION AND RELATED OBJECTS FROM CSPACE-SERVICES
        #################################################################

        #  get e-loan list-item
        asquery = '%s?as=%s_common%%3AloanOutNumber%%3D%%27%s%%27&wf_deleted=false' % (recType, recType, eloanNum,)

        expectedmimetype = 'application/xml'

        # Make authenticated connection to ucjeps.cspace...
        lolistdata = get_entity(request, asquery, expectedmimetype)
        if lolistdata is None:
            errMsg = 'Sorry, I can\'t talk to CSpace so I can\'t help you with your eloan. Please contact the administrator.'
            return render(request, 'eloan.html',
                            {'results': errMsg, 'displayType': 'error', 'title': TITLE, 'timestamp': TIMESTAMP }
                    )
        lolistdata = lolistdata.content
        loanoutlistXML = fromstring(lolistdata)

        # To grab everything: loinfo = loanoutlistXML.find('.//list-item')
        # To grab just the Loanout CSID:

        locsid = loanoutlistXML.find('.//list-item/csid')
        if locsid is None:
            errMsg = 'Error: We could not find the loan \'%s.\' Please try another.' % eloanNum
            return render(request, 'eloan.html',
                          {'results': errMsg, 'displayType': 'error', 'title': TITLE, 'timestamp': TIMESTAMP }
            )
        locsid = locsid.text

        # get e-loan record
        loquery = '%s/%s' % (recType, locsid)

        # Make authenticated connection to ucjeps.cspace...
        try:
            lodata = get_entity(request, loquery, expectedmimetype).content
            loanoutXML = fromstring(lodata)

        except urllib2.HTTPError, e:
            print 'Error2.'
            return

        # Start gathering loan out info into results: loan number (already have), borrower's contact and loan date.
        loaninfo = []
        loaninfo.append(eloanNum)

        borrower = getInstitutionCodefromDisplayName(loanoutXML, './/borrower')
        if borrower == '':
            borrower = getShortIdfromRefName(loanoutXML, './/borrower')
        if re.match(".*\d{13}", borrower):
            borrower = getfromXML(loanoutXML, './/borrower')
        loaninfo.append(borrower)

        #borcontact = getfromXML(loanoutXML, './/borrowersContact')
        #loaninfo.append(borcontact)

        lodate = getfromXML(loanoutXML, './/loanOutDate')
        loaninfo.append(lodate)

        # Get list of collection objects included in the loan out as Loan Out Items.
        loitemsXML = loanoutXML.findall('.//objectGroupList/objectGroup/objectNumbers')

        objectNumbers = []

        # In case UCJEPS staff have not listed any loan out items (e.g., they've related the cataloging records instead)
        if loitemsXML == []:
            errMsg = 'Error: You have requested a loan that contains no specimens. Please have the herbarium staff check the loan.'
            return render(request, 'eloan.html',
                            {'loaninfo': loaninfo, 'results': errMsg, 'displayType': 'error', 'title': TITLE, 'timestamp': TIMESTAMP }
                    )

        # In case primary repeatable group under Loan Out Items has no value in the object number field
        elif loitemsXML[0].text is None:
            errMsg = 'Error: You have requested a loan that contains a record with no Specimen ID. Please have the herbarium staff check the loan.'
            return render(request, 'eloan.html',
                            {'loaninfo': loaninfo, 'results': errMsg, 'displayType': 'error', 'title': TITLE, 'timestamp': TIMESTAMP }
                    )

        elif loitemsXML[0].text:
            for loitem in loitemsXML:
                objNum = loitem.text
                if objNum is None:
                    objNum = ''
                if objNum == '':
                    errMsg = 'Error: You have requested a loan that contains a record with no Specimen ID. Please have the herbarium staff check the loan.'
                    return render(request, 'eloan.html',
                                    {'loaninfo': loaninfo, 'results': errMsg, 'displayType': 'error', 'title': TITLE, 'timestamp': TIMESTAMP }
                            )
                objectNumbers.append(objNum)

            # Other options ... if we ever need to search by CSID or objectName
            # Note: CSIDs are passed in URL but do not appear on public search form
            #objCsid = getfromXML(i, './object/csid')
            #objectCsids.append(objCsid)

            # Note: ObjectName not necessarily unique, so using it for search is problematic
            #objName = getfromXML(i,'./object/name')
            #objectNames.append(objName)


        #################################################
        # CALL PUBLICSEARCH WEBAPP, DISPLAY SEARCH RESULTS IN A DIV BELOW LOAN OUT INFO
        # TODO: Need to incorporate typeSpecimenBasionym field into solr data source and template.
        #################################################

        results = {}

        # Args to pass to solr - REQUIRED
        solr_server = SOLRSERVER
        solr_core = SOLRCORE
        solr_queryparam_key = SOLRQUERYPARAM
        # Pull individual objectNumbers from list and insert ' OR ' between each
        solr_queryparam_value = " OR ".join(objectNumbers)

        # Search public search (solr) portal
        results = build_solr_query(solr_server, solr_core, solr_queryparam_key, solr_queryparam_value)

        labels = {}
        for p in PARMS:
            labels[p] = PARMS[p][0]


        # Either break values out of results array as we do here, or use results[value] notation in HTML templates
        return render(request, 'eloan.html',
                      {'loaninfo': loaninfo, 'results': results, 'items': results['items'],
                       'displayType': results['displayType'], 'count': results['count'],
                       'imageserver': results['imageserver'], 'url': results['url'],
                       'querystring': results['querystring'], 'timestamp': results['timestamp'],
                       'time': results['time'], 'labels': labels, 'kw': eloanNum, 'title': TITLE }
        )

    else:
        # Include a bit of instruction to the user
        emptyMsg = 'Please enter a loan number'
        TIMESTAMP = time.strftime("%b %d %Y %H:%M:%S", time.localtime())
        return render(request, 'eloan.html', {'title': TITLE, 'timestamp': TIMESTAMP, 'results': emptyMsg, 'displayType': 'empty'}
        )
