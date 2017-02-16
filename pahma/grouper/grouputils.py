import re
import sys
import time
from django.shortcuts import render, render_to_response, redirect
import urllib
import urllib2
from cspace_django_site.main import cspace_django_site
from common import cspace
from toolbox.cswaUtils import relationsPayload


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

def add2group(groupcsid, list_of_objects, request):
    connection = cspace.connection.create_connection(config, request.user)
    uri = 'cspace-services/relations'
    messages = []

    for object in list_of_objects:
        messages.append("posting group2obj to relations REST API...")

        # "urn:cspace:institution.cspace.berkeley.edu:group:id(%s)" % groupCSID
        groupElements = {}
        groupElements['objectDocumentType'] = 'CollectionObject'
        groupElements['subjectDocumentType'] = 'Group'
        groupElements['objectCsid'] = object
        groupElements['subjectCsid'] = groupcsid

        payload = relationsPayload(groupElements)
        (url, data, csid, elapsedtime) = connection.postxml(uri=uri, payload=payload, requesttype="POST")
        # elapsedtimetotal += elapsedtime
        messages.append('got relation csid %s elapsedtime %s ' % (csid, elapsedtime))
        groupElements['group2objCSID'] = csid
        messages.append("relations REST API post succeeded...")

        # reverse the roles
        messages.append("posting obj2group to relations REST API...")
        temp = groupElements['objectCsid']
        groupElements['objectCsid'] = groupElements['subjectCsid']
        groupElements['subjectCsid'] = temp
        groupElements['objectDocumentType'] = 'Group'
        groupElements['subjectDocumentType'] = 'CollectionObject'
        payload = relationsPayload(groupElements)
        (url, data, csid, elapsedtime) = connection.postxml(uri=uri, payload=payload, requesttype="POST")
        # elapsedtimetotal += elapsedtime
        messages.append('got relation csid %s elapsedtime %s ' % (csid, elapsedtime))
        groupElements['obj2groupCSID'] = csid
        messages.append("relations REST API post succeeded...")

    return messages


def create_group(grouptitle, request):
    payload = """
        <document name="groups">
            <ns2:groups_common xmlns:ns2="http://collectionspace.org/services/group" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
                <title>%s</title>
            </ns2:groups_common>
        </document>
        """ % grouptitle

    connection = cspace.connection.create_connection(config, request.user)
    (url, data, csid, elapsedtime) = connection.postxml(uri='cspace-services/groups', payload=payload, requesttype="POST")
    return csid


def getfromCSpace(uri, request):
    connection = cspace.connection.create_connection(config, request.user)
    url = "cspace-services/" + uri
    return connection.make_get_request(url)


def find_group(request, grouptitle):

    TIMESTAMP = time.strftime("%b %d %Y %H:%M:%S", time.localtime())

    asquery = '%s?as=%s_common%%3Atitle%%3D%%27%s%%27&wf_deleted=false' % ('groups', 'groups', grouptitle,)

    #expectedmimetype = 'application/xml'

    # Make authenticated connection to ucjeps.cspace...
    (groupurl, grouprecord, x) = getfromCSpace(asquery, request)
    if grouprecord is None:
        return(None, None, 'Error: We could not find the group \'%s.\' Please try another.' % grouptitle)
    grouprecordtree = fromstring(grouprecord)

    groupcsid = grouprecordtree.find('.//csid')
    if groupcsid is None:
        return(None, None, 'Error: We could not find the group \'%s.\' Please try another.' % grouptitle)
    groupcsid = groupcsid.text

    uri = 'collectionobjects?rtObj=%s' % groupcsid
    # Make authenticated connection to ucjeps.cspace...
    try:
        (groupurl, groupmembers, x) = getfromCSpace(uri, request)
        groupmembers = fromstring(groupmembers)
        objectcsids = [e.text for e in groupmembers.findall('.//csid')]
    except urllib2.HTTPError, e:
        print 'Error2.'
        objectcsids = []

    return (grouptitle, groupcsid, objectcsids)