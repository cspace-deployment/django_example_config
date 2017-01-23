#!/usr/bin/env /usr/bin/python
# -*- coding: UTF-8 -*-

import os
import copy

# for log
import csv
import json
import codecs
import ConfigParser

import time, datetime
import urllib2
import re

from dirq.QueueSimple import QueueSimple
DIRQ = QueueSimple('/tmp/cswa')
WHEN2POST = 'queue'

MAXLOCATIONS = 1000

try:
    import xml.etree.ElementTree as etree
    #print("running with ElementTree")
except ImportError:
    try:
        from lxml import etree
        #print("running with lxml.etree")
    except ImportError:
        try:
            # normal cElementTree install
            import cElementTree as etree
            #print("running with cElementTree")
        except ImportError:
            try:
                # normal ElementTree install
                import elementtree.ElementTree as etree
                #print("running with ElementTree")
            except ImportError:
                print("Failed to import ElementTree from any known place")


from cswaHelpers import *
from common import cspace
from cspace_django_site.main import cspace_django_site

MAINCONFIG = cspace_django_site.getConfig()

def updateCspace(fieldset, updateItems, form):

    connection = cspace.connection.create_connection(MAINCONFIG, form['userdata'])

    message = ''

    uri = 'collectionobjects'
    getItems = updateItems['objectCsid']
    if getItems == None:
        url = "cspace-services/%s" % uri
    else:
        url = "cspace-services/%s/%s" % (uri, getItems)

    #Fields vary with fieldsets
    if fieldset == 'keyinfo':
        fieldList = ('pahmaFieldCollectionPlace', 'assocPeople', 'objectName', 'pahmaEthnographicFileCode')
    elif fieldset == 'namedesc':
        fieldList = ('briefDescription', 'objectName')
    elif fieldset == 'registration':
        # nb:  'pahmaAltNumType' is handled with  'pahmaAltNum'
        fieldList = ('objectName', 'pahmaAltNum', 'fieldCollector')
    elif fieldset == 'hsrinfo':
        fieldList = ('objectName', 'pahmaFieldCollectionPlace', 'briefDescription')
    elif fieldset == 'objtypecm':
        fieldList = ('objectName', 'collection', 'responsibleDepartment', 'pahmaFieldCollectionPlace')
    elif fieldset == 'collection':
        fieldList = ('objectName', 'collection')
    elif fieldset == 'placeanddate':
        fieldList = ('pahmaFieldLocVerbatim', 'pahmaFieldCollectionDate')


    # get the XML for this object getxml

    url, content, elapsedtime = connection.make_get_request(url)
    root = etree.fromstring(content)
    # add the user's changes to the XML
    for relationType in fieldList:
        #sys.stderr.write('tag1: %s\n' % relationType)
        # this app does not insert empty values into anything!
        if not relationType in updateItems.keys() or updateItems[relationType] == '':
            continue
        listSuffix = 'List'
        extra = ''
        if relationType in ['assocPeople', 'pahmaAltNum', 'pahmaFieldCollectionDate']:
            extra = 'Group'
        elif relationType in ['briefDescription', 'fieldCollector', 'responsibleDepartment']:
            listSuffix = 's'
        elif relationType in ['collection', 'pahmaFieldLocVerbatim']:
            listSuffix = ''
        else:
            pass
            #html += ">>> ",'.//'+relationType+extra+'List'
        #sys.stderr.write('tag2: %s\n' % (relationType + extra + listSuffix))
        metadata = root.findall('.//' + relationType + extra + listSuffix)
        try:
            metadata = metadata[0] # there had better be only one!
        except:
            # hmmm ... we didn't find this element in the record. Make a note a carry on!
            # message += 'No "' + relationType + extra + listSuffix + '" element found to update.'
            continue
        #print(etree.tostring(metadata))
        #html += ">>> ",relationType,':',updateItems[relationType]
        if relationType in ['assocPeople', 'objectName', 'pahmaAltNum']:
            #group = metadata.findall('.//'+relationType+'Group')
            #sys.stderr.write('  updateItem: ' + relationType + ':: ' + updateItems[relationType] + '\n' )
            Entries = metadata.findall('.//' + relationType)
            if not alreadyExists(updateItems[relationType], Entries):
                newElement = etree.Element(relationType + 'Group')
                leafElement = etree.Element(relationType)
                leafElement.text = updateItems[relationType]
                newElement.append(leafElement)
                if relationType in ['assocPeople', 'pahmaAltNum']:
                    apgType = etree.Element(relationType + 'Type')
                    apgType.text = updateItems[relationType + 'Type'].lower() if relationType == 'pahmaAltNum' else 'made by'
                    #sys.stderr.write(relationType + 'Type:' + updateItems[relationType + 'Type'])
                    newElement.append(apgType)
                if len(Entries) == 1 and Entries[0].text is None:
                    #sys.stderr.write('reusing empty element: %s\n' % Entries[0].tag)
                    #sys.stderr.write('ents : %s\n' % Entries[0].text)
                    #html += '<br>before',etree.tostring(metadata).replace('<','&lt;').replace('>','&gt;')
                    for child in metadata:
                        #html += '<br>tag: ', child.tag
                        if child.tag == relationType + 'Group':
                            #html += '<br> found it! ',child.tag
                            metadata.remove(child)
                    metadata.insert(0,newElement)
                    #html += '<br>after',etree.tostring(metadata).replace('<','&lt;').replace('>','&gt;')
                else:
                    metadata.insert(0,newElement)
            else:
                if IsAlreadyPreferred(updateItems[relationType], metadata.findall('.//' + relationType)):
                    continue
                else:
                    # exists, but not preferred. make it the preferred: remove it from where it is, insert it as 1st
                    for child in metadata:
                        if child.tag == relationType + 'Group':
                            checkval = child.find('.//' + relationType)
                            if checkval.text == updateItems[relationType]:
                                savechild = child
                                metadata.remove(child)
                    metadata.insert(0,savechild)
                pass
            # for AltNums, we need to update the AltNumType even if the AltNum hasn't changed
            if relationType == 'pahmaAltNum':
                apgType = metadata.find('.//' + relationType + 'Type')
                apgType.text = updateItems[relationType + 'Type']
                #sys.stderr.write('  updated: pahmaAltNumType to' + updateItems[relationType + 'Type'] + '\n' )
        elif relationType in ['briefDescription', 'fieldCollector', 'responsibleDepartment']:
            Entries = metadata.findall('.//' + relationType)
            #for e in Entries:
                #html += '%s, %s<br>' % (e.tag, e.text)
                #sys.stderr.write(' e: %s\n' % e.text)
            if alreadyExists(updateItems[relationType], Entries):
                if IsAlreadyPreferred(updateItems[relationType], Entries):
                    # message += "%s exists as %s, already preferred;" % (updateItems[relationType],relationType)
                    pass
                else:
                    # exists, but not preferred. make it the preferred: remove it from where it is, insert it as 1st
                    for child in Entries:
                        sys.stderr.write(' c: %s\n' % child.tag)
                        if child.text == updateItems[relationType]:
                            new_element = child
                            metadata.remove(child)
                            # message += '%s removed. len = %s<br/>' % (child.text, len(Entries))
                    metadata.insert(0,new_element)
                    message += " %s exists in %s, now preferred.<br/>" % (updateItems[relationType],relationType)
                    #html += 'already exists: %s<br>' % updateItems[relationType]
            # check if the existing element is empty; if so, use it, don't add a new element
            else:
                if len(Entries) == 1 and Entries[0].text is None:
                    #message += "removed %s ;<br/>" % (Entries[0].tag)
                    metadata.remove(Entries[0])
                new_element = etree.Element(relationType)
                new_element.text = updateItems[relationType]
                metadata.insert(0,new_element)
                message += "added preferred term %s as %s.<br/>" % (updateItems[relationType],relationType)

        elif relationType in ['pahmaFieldCollectionDate']:
            # we'll be replacing the entire structured date group
            pahmaFieldCollectionDateGroup = metadata.find('.//pahmaFieldCollectionDateGroup')
            newpahmaFieldCollectionDateGroup = etree.Element('pahmaFieldCollectionDateGroup')
            new_element = etree.Element('dateDisplayDate')
            new_element.text = updateItems[relationType]
            newpahmaFieldCollectionDateGroup.insert(0,new_element)
            if pahmaFieldCollectionDateGroup is not None:
                metadata.remove(pahmaFieldCollectionDateGroup)
            metadata.insert(0,newpahmaFieldCollectionDateGroup)

        else:
            # check if value is already present. if so, skip
            if alreadyExists(updateItems[relationType], metadata.findall('.//' + relationType)):
                if IsAlreadyPreferred(updateItems[relationType], metadata.findall('.//' + relationType)):
                    continue
                else:
                    message += "%s: %s already exists. Now duplicated with this as preferred.<br/>" % (relationType,updateItems[relationType])
                    pass
            newElement = etree.Element(relationType)
            newElement.text = updateItems[relationType]
            metadata.insert(0, newElement)
            #print(etree.tostring(metadata, pretty_print=True))
    objectCount = root.find('.//numberOfObjects')
    if 'objectCount' in updateItems:
        if objectCount is None:
            objectCount = etree.Element('numberOfObjects')
            collectionobjects_common = root.find(
                './/{http://collectionspace.org/services/collectionobject}collectionobjects_common')
            collectionobjects_common.insert(0, objectCount)
        objectCount.text = updateItems['objectCount']

    inventoryCount = root.find('.//inventoryCount')
    if 'inventoryCount' in updateItems:
        if inventoryCount is None:
            inventoryCount = etree.Element('inventoryCount')
            collectionobjects_pahma = root.find(
                './/{http://collectionspace.org/services/collectionobject/local/pahma}collectionobjects_pahma')
            collectionobjects_pahma.insert(0, inventoryCount)
        inventoryCount.text = updateItems['inventoryCount']
    #print(etree.tostring(root, pretty_print=True))

    if 'pahmaFieldLocVerbatim' in updateItems:
        pahmaFieldLocVerbatim = root.find('.//pahmaFieldLocVerbatim')
        if pahmaFieldLocVerbatim is None:
            pahmaFieldLocVerbatim = etree.Element('pahmaFieldLocVerbatim')
            pahmaFieldLocVerbatimobjects_common = root.find(
                './/{http://collectionspace.org/services/collectionobject/local/pahma}collectionobjects_pahma')
            pahmaFieldLocVerbatimobjects_common.insert(0, pahmaFieldLocVerbatim)
            message += " %s added as &lt;%s&gt;.<br/>" % (updateItems['pahmaFieldLocVerbatim'], 'pahmaFieldLocVerbatim')
        pahmaFieldLocVerbatim.text = updateItems['pahmaFieldLocVerbatim']

    collection = root.find('.//collection')
    if 'collection' in updateItems:
        if collection is None:
            collection = etree.Element('collection')
            collectionobjects_common = root.find(
                './/{http://collectionspace.org/services/collectionobject}collectionobjects_common')
            collectionobjects_common.insert(0, collection)
            message += " %s added as &lt;%s&gt;.<br/>" % (updateItems['collection'], 'collection')
        collection.text = updateItems['collection']



    uri = 'collectionobjects' + '/' + updateItems['objectCsid']
    payload = '<?xml version="1.0" encoding="UTF-8"?>\n' + etree.tostring(root,encoding='utf-8')
    # update collectionobject..
    #html += "<br>pretending to post update to %s to REST API..." % updateItems['objectCsid']
    elapsedtimetotal = time.time()
    messages = []
    messages.append("posting to %s REST API..." % uri)
    #print payload
    # messages.append(payload)
    (url, data, csid, elapsedtime) = postxml('PUT', uri, payload, form)

    return message

    #html += "<h3>Done w update!</h3>"


def createObject(objectinfo, config, form):

    message = ''

    uri = 'collectionobjects'

    # get the XML for this object
    content = '''<document name="collectionobjects">
<ns2:collectionobjects_common xmlns:ns2="http://collectionspace.org/services/collectionobject" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
<objectNameList>
<objectNameGroup>
<objectName/>
</objectNameGroup>
</objectNameList>
<objectNumber/>
</ns2:collectionobjects_common>
</document>'''

    x = '''
<ns2:collectionobjects_omca xmlns:ns2="http://collectionspace.org/services/collectionobject/local/omca" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
<sortableObjectNumber/>
</ns2:collectionobjects_omca>
'''

    root = etree.fromstring(content)
    for elementname in objectinfo:
        if elementname in objectinfo:
            element = root.find('.//' + elementname)
            element.text = objectinfo[elementname]

    uri = 'collectionobjects'
    payload = '<?xml version="1.0" encoding="UTF-8"?>\n' + etree.tostring(root,encoding='utf-8')
    # update collectionobject..
    sys.stderr.write("post new object %s to REST API..." % objectinfo['objectNumber'])
    #sys.stderr.write(etree.tostring(root))
    (url, data, csid, elapsedtime) = postxml('POST', uri, payload, form)
    sys.stderr.write("created new object with csid %s to REST API..." % csid)
    writeLog(objectinfo, uri, 'POST', '', config)
    # message = 'succeeded'

    return message, csid

    #html += "<h3>Done w update!</h3>"


def updateLocations(updateItems, config, form):
    institution = config.get('info', 'institution')

    uri = 'movements'

    #html += "<br>posting to movements REST API..."
    payload = lmiPayload(updateItems, institution)
    (url, data, csid, elapsedtime) = postxml('POST', uri, payload, form)
    updateItems['subjectCsid'] = csid

    uri = 'relations'

    #html += "<br>posting inv2obj to relations REST API..."
    updateItems['subjectDocumentType'] = 'Movement'
    updateItems['objectDocumentType'] = 'CollectionObject'
    payload = relationsPayload(updateItems)
    (url, data, csid, elapsedtime) = postxml('POST', uri, payload, form)

    # reverse the roles
    #html += "<br>posting obj2inv to relations REST API..."
    temp = updateItems['objectCsid']
    updateItems['objectCsid'] = updateItems['subjectCsid']
    updateItems['subjectCsid'] = temp
    updateItems['subjectDocumentType'] = 'CollectionObject'
    updateItems['objectDocumentType'] = 'Movement'
    payload = relationsPayload(updateItems)
    (url, data, csid, elapsedtime) = postxml('POST', uri, payload, form)

    writeLog(updateItems, uri, 'POST', '', config)

    #html += "<h3>Done w update!</h3>"


def getxml(uri, realm, hostname, username, password, getItems):
    # port and protocol need to find their ways into the config files...
    port = ''
    protocol = 'https'
    server = protocol + "://" + hostname + port
    passman = urllib2.HTTPPasswordMgr()
    passman.add_password(realm, server, username, password)
    authhandler = urllib2.HTTPBasicAuthHandler(passman)
    opener = urllib2.build_opener(authhandler)
    urllib2.install_opener(opener)
    if getItems == None:
        url = "%s/cspace-services/%s" % (server, uri)
    else:
        url = "%s/cspace-services/%s/%s" % (server, uri, getItems)
    #sys.stderr.write('url %s' % url )
    elapsedtime = 0.0

    try:
        elapsedtime = time.time()
        f = urllib2.urlopen(url)
        data = f.read()
        elapsedtime = time.time() - elapsedtime
    except urllib2.HTTPError, e:
        sys.stderr.write('The server couldn\'t fulfill the request.')
        sys.stderr.write( 'Error code: %s' % e.code)
        raise
    except urllib2.URLError, e:
        sys.stderr.write('We failed to reach a server.')
        sys.stderr.write( 'Reason: %s' % e.reason)
        raise
    else:
        return (url, data, elapsedtime)

        #data = "\n<h3>%s :: %s</h3>" % e


def postxml(requestType, uri, payload, form):
    if WHEN2POST == 'now':
        connection = cspace.connection.create_connection(MAINCONFIG, form['userdata'])
        try:
            return connection.postxml(uri="cspace-services/"+uri, payload=payload, requesttype=requestType)
        except:
            raise
            return "%s REST API post failed..." % uri
        #return post2xml(requestType, uri, payload)
    else:
        return post2queue(requestType, uri, payload)


def post2queue(requestType, uri, payload):
    # relations records have dependencies -- these are handled by the queue consumer
    if uri != 'relations':
        element = json.dumps((requestType, uri, payload))
        DIRQ.add(element)
    return ('url', 'data', 'queued', 0.00)


# def post2xml(requestType, uri, realm, hostname, username, password, payload):
#     port = ''
#     protocol = 'https'
#     server = protocol + "://" + hostname + port
#     passman = urllib2.HTTPPasswordMgr()
#     passman.add_password(realm, server, username, password)
#     authhandler = urllib2.HTTPBasicAuthHandler(passman)
#     opener = urllib2.build_opener(authhandler)
#     urllib2.install_opener(opener)
#     url = "%s/cspace-services/%s" % (server, uri)
#     elapsedtime = 0.0
#
#     elapsedtime = time.time()
#     request = urllib2.Request(url, payload, {'Content-Type': 'application/xml'})
#     # default method for urllib2 with payload is POST
#     if requestType == 'PUT': request.get_method = lambda: 'PUT'
#     try:
#         f = urllib2.urlopen(request)
#     except urllib2.URLError, e:
#         if hasattr(e, 'reason'):
#             sys.stderr.write('We failed to reach a server.\n')
#             sys.stderr.write('Reason: ' + str(e.reason) + '\n')
#         if hasattr(e, 'code'):
#             sys.stderr.write('The server couldn\'t fulfill the request.\n')
#             sys.stderr.write('Error code: ' + str(e.code) + '\n')
#         if True:
#             #html += 'Error in POSTing!'
#             sys.stderr.write("Error in POSTing!\n")
#             sys.stderr.write(url)
#             sys.stderr.write(payload)
#             raise
#
#     data = f.read()
#     info = f.info()
#     # if a POST, the Location element contains the new CSID
#     if info.getheader('Location'):
#         csid = re.search(uri + '/(.*)', info.getheader('Location'))
#         csid = csid.group(1)
#     else:
#         csid = ''
#     elapsedtime = time.time() - elapsedtime
#     return (url, data, csid, elapsedtime)


def writeLog(updateItems, uri, httpAction, username, config):
    auditFile = config.get('files', 'auditfile')
    updateType = config.get('info', 'updatetype')
    # myPid = str(os.getpid())
    # writing of individual log files is now disabled. audit file contains the same data.
    #logFile = config.get('files','logfileprefix') + '.' + datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S") + myPid + '.csv'

    # yes, it is inefficient open the log to write each row, but in the big picture, it's insignificant
    try:
        #csvlogfh = csv.writer(codecs.open(logFile,'a','utf-8'), delimiter="\t")
        #csvlogfh.writerow([updateItems['locationDate'],updateItems['objectNumber'],updateItems['objectStatus'],updateItems['subjectCsid'],updateItems['objectCsid'],updateItems['handlerRefName']])
        csvlogfh = csv.writer(codecs.open(auditFile, 'a', 'utf-8'), delimiter="\t")
        logrec = [ httpAction, datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"), updateType, uri, username ]
        for item in updateItems.keys():
            logrec.append("%s=%s" % (item, updateItems[item].replace('\n','#')))
        csvlogfh.writerow(logrec)
    except:
        raise
        #html += 'writing to log %s failed!' % auditFile
        pass


def writeInfo2log(request, form, config, elapsedtime):
    location1 = str(form.get("lo.location1"))
    action = str(form.get("action"))
    serverlabel = config.get('info', 'serverlabel')
    apptitle = config.get('info', 'apptitle')
    updateType = config.get('info', 'updatetype')
    institution = config.get('info', 'institution')
    checkServer = form.get('check')
    # override updateType if we are just checking the server
    if checkServer == 'check server':
        updateType = checkServer
    # sys.stderr.write('%-13s:: %-18s:: %-6s::%8.2f :: %-15s :: %s :: %s\n' % (updateType, action, request, elapsedtime, serverlabel))
    updateItems = {'app': apptitle, 'server': serverlabel, 'institution': institution, 'elapsedtime': '%8.2f' % elapsedtime, 'action': action}
    writeLog(updateItems, '', request, '', config)