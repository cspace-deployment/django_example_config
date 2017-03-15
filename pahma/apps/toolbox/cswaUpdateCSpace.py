#!/usr/bin/env /usr/bin/python
# -*- coding: UTF-8 -*-

import json
import codecs
import time
import datetime
import csv

from dirq.QueueSimple import QueueSimple

from cswaHelpers import *
from common import cspace
from cspace_django_site.main import cspace_django_site

MAINCONFIG = cspace_django_site.getConfig()

DIRQ = QueueSimple('/tmp/cswa')

MAXLOCATIONS = 1000

try:
    import xml.etree.ElementTree as etree
    # print("running with ElementTree")
except ImportError:
    try:
        from lxml import etree
        # print("running with lxml.etree")
    except ImportError:
        try:
            # normal cElementTree install
            import cElementTree as etree
            # print("running with cElementTree")
        except ImportError:
            try:
                # normal ElementTree install
                import elementtree.ElementTree as etree
                # print("running with ElementTree")
            except ImportError:
                print("Failed to import ElementTree from any known place")


def add2queue(requestType, uri, fieldset, updateItems, form):
    userdata = form['userdata']
    element = json.dumps((requestType, uri, userdata.username, userdata.cspace_password, fieldset, updateItems))
    DIRQ.add(element)


def updateCspace(fieldset, updateItems, form, config, when2post):
    uri = 'collectionobjects' + '/' + updateItems['objectCsid']
    writeLog(updateItems, uri, 'POST', form, config)

    if when2post == 'now':
        # get the XML for this object
        connection = cspace.connection.create_connection(MAINCONFIG, form['userdata'])
        url = "cspace-services/" + uri
        url2, content, elapsedtime = connection.make_get_request(url)
        message, payload = updateXML(fieldset, updateItems, content)
        (url3, data, csid, elapsedtime) = postxml('PUT', uri, payload, form)
        sys.stderr.write("updated object with csid %s to REST API..." % updateItems['objectCsid'])
        return ''
    elif when2post == 'queue':
        add2queue("PUT", uri, fieldset, updateItems, form)
        return ''
    else:
        raise


def createObject(objectinfo, config, form, when2post):
    uri = 'collectionobjects'
    writeLog(objectinfo, uri, 'POST', form, config)

    if when2post == 'now':
        payload = createObjectXML(objectinfo)
        (url, data, csid, elapsedtime) = postxml('POST', uri, payload, form)
        sys.stderr.write("created new object with csid %s to REST API..." % csid)
        return 'created new object', csid
    elif when2post == 'queue':
        add2queue("POST", uri, 'createobject', objectinfo, form)
        return 'queued new object', ''
    else:
        raise


def updateLocations(updateItems, config, form, when2post):
    uri = 'movements'
    writeLog(updateItems, uri, 'POST', form, config)

    if when2post == 'now':
        makeMH2R(updateItems, config, form)
        return 'moved', ''
    elif when2post == 'queue':
        add2queue("POST", uri, 'movements', updateItems, form)
        return 'queued move', ''
    else:
        raise


def updateXML(fieldset, updateItems, xml):
    message = ''

    # Fields vary with fieldsets
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

    root = etree.fromstring(xml)
    # add the user's changes to the XML
    for relationType in fieldList:
        # sys.stderr.write('tag1: %s\n' % relationType)
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
            # html += ">>> ",'.//'+relationType+extra+'List'
        # sys.stderr.write('tag2: %s\n' % (relationType + extra + listSuffix))
        metadata = root.findall('.//' + relationType + extra + listSuffix)
        if 'objectNumber' in updateItems and updateItems['objectNumber'] == '':
            updateItems['objectNumber'] = root.find('.//objectNumber').text
        try:
            metadata = metadata[0]  # there had better be only one!
        except:
            # hmmm ... we didn't find this element in the record. Make a note a carry on!
            # message += 'No "' + relationType + extra + listSuffix + '" element found to update.'
            continue
        # print(etree.tostring(metadata))
        # html += ">>> ",relationType,':',updateItems[relationType]
        if relationType in ['assocPeople', 'objectName', 'pahmaAltNum']:
            # group = metadata.findall('.//'+relationType+'Group')
            # sys.stderr.write('  updateItem: ' + relationType + ':: ' + updateItems[relationType] + '\n' )
            Entries = metadata.findall('.//' + relationType)
            if not alreadyExists(updateItems[relationType], Entries):
                newElement = etree.Element(relationType + 'Group')
                leafElement = etree.Element(relationType)
                leafElement.text = updateItems[relationType]
                newElement.append(leafElement)
                if relationType in ['assocPeople', 'pahmaAltNum']:
                    apgType = etree.Element(relationType + 'Type')
                    apgType.text = updateItems[
                        relationType + 'Type'].lower() if relationType == 'pahmaAltNum' else 'made by'
                    # sys.stderr.write(relationType + 'Type:' + updateItems[relationType + 'Type'])
                    newElement.append(apgType)
                if len(Entries) == 1 and Entries[0].text is None:
                    # sys.stderr.write('reusing empty element: %s\n' % Entries[0].tag)
                    # sys.stderr.write('ents : %s\n' % Entries[0].text)
                    # html += '<br>before',etree.tostring(metadata).replace('<','&lt;').replace('>','&gt;')
                    for child in metadata:
                        # html += '<br>tag: ', child.tag
                        if child.tag == relationType + 'Group':
                            # html += '<br> found it! ',child.tag
                            metadata.remove(child)
                    metadata.insert(0, newElement)
                    # html += '<br>after',etree.tostring(metadata).replace('<','&lt;').replace('>','&gt;')
                else:
                    metadata.insert(0, newElement)
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
                    metadata.insert(0, savechild)
                pass
            # for AltNums, we need to update the AltNumType even if the AltNum hasn't changed
            if relationType == 'pahmaAltNum':
                apgType = metadata.find('.//' + relationType + 'Type')
                apgType.text = updateItems[relationType + 'Type']
                # sys.stderr.write('  updated: pahmaAltNumType to' + updateItems[relationType + 'Type'] + '\n' )
        elif relationType in ['briefDescription', 'fieldCollector', 'responsibleDepartment']:
            Entries = metadata.findall('.//' + relationType)
            # for e in Entries:
            # html += '%s, %s<br>' % (e.tag, e.text)
            # sys.stderr.write(' e: %s\n' % e.text)
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
                    metadata.insert(0, new_element)
                    message += " %s exists in %s, now preferred.<br/>" % (updateItems[relationType], relationType)
                    # html += 'already exists: %s<br>' % updateItems[relationType]
            # check if the existing element is empty; if so, use it, don't add a new element
            else:
                if len(Entries) == 1 and Entries[0].text is None:
                    # message += "removed %s ;<br/>" % (Entries[0].tag)
                    metadata.remove(Entries[0])
                new_element = etree.Element(relationType)
                new_element.text = updateItems[relationType]
                metadata.insert(0, new_element)
                message += "added preferred term %s as %s.<br/>" % (updateItems[relationType], relationType)

        elif relationType in ['pahmaFieldCollectionDate']:
            # we'll be replacing the entire structured date group
            pahmaFieldCollectionDateGroup = metadata.find('.//pahmaFieldCollectionDateGroup')
            newpahmaFieldCollectionDateGroup = etree.Element('pahmaFieldCollectionDateGroup')
            new_element = etree.Element('dateDisplayDate')
            new_element.text = updateItems[relationType]
            newpahmaFieldCollectionDateGroup.insert(0, new_element)
            if pahmaFieldCollectionDateGroup is not None:
                metadata.remove(pahmaFieldCollectionDateGroup)
            metadata.insert(0, newpahmaFieldCollectionDateGroup)

        else:
            # check if value is already present. if so, skip
            if alreadyExists(updateItems[relationType], metadata.findall('.//' + relationType)):
                if IsAlreadyPreferred(updateItems[relationType], metadata.findall('.//' + relationType)):
                    continue
                else:
                    message += "%s: %s already exists. Now duplicated with this as preferred.<br/>" % (
                        relationType, updateItems[relationType])
                    pass
            newElement = etree.Element(relationType)
            newElement.text = updateItems[relationType]
            metadata.insert(0, newElement)
            # print(etree.tostring(metadata, pretty_print=True))
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
    # print(etree.tostring(root, pretty_print=True))

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

    payload = '<?xml version="1.0" encoding="UTF-8"?>\n' + etree.tostring(root, encoding='utf-8')
    # update collectionobject..
    # html += "<br>pretending to post update to %s to REST API..." % updateItems['objectCsid']
    # elapsedtimetotal = time.time()
    # messages = []
    # messages.append("posting to %s REST API..." % uri)
    # print payload
    # messages.append(payload)

    return message, payload


def createObjectXML(objectinfo):

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
    payload = '<?xml version="1.0" encoding="UTF-8"?>\n' + etree.tostring(root, encoding='utf-8')
    # update collectionobject..
    # sys.stderr.write("post new object %s to REST API..." % objectinfo['objectNumber'])
    # sys.stderr.write(etree.tostring(root))

    return '', payload


def makeMH2R(updateItems, config, form):
    institution = config.get('info', 'institution')

    uri = 'movements'

    # html += "<br>posting to movements REST API..."
    payload = lmiPayload(updateItems, institution)
    (url, data, csid, elapsedtime) = postxml('POST', uri, payload, form)
    updateItems['subjectCsid'] = csid

    uri = 'relations'

    # html += "<br>posting inv2obj to relations REST API..."
    updateItems['subjectDocumentType'] = 'Movement'
    updateItems['objectDocumentType'] = 'CollectionObject'
    payload = relationsPayload(updateItems)
    (url, data, ignorecsid, elapsedtime) = postxml('POST', uri, payload, form)

    # reverse the roles
    # html += "<br>posting obj2inv to relations REST API..."
    temp = updateItems['objectCsid']
    updateItems['objectCsid'] = updateItems['subjectCsid']
    updateItems['subjectCsid'] = temp
    updateItems['subjectDocumentType'] = 'CollectionObject'
    updateItems['objectDocumentType'] = 'Movement'
    payload = relationsPayload(updateItems)
    (url, data, ignorecsid, elapsedtime) = postxml('POST', uri, payload, form)

    writeLog(updateItems, uri, 'POST', form, config)

    # html += "<h3>Done w update!</h3>"


def postxml(requestType, uri, payload, form):
    connection = cspace.connection.create_connection(MAINCONFIG, form['userdata'])
    try:
        return connection.postxml(uri="cspace-services/" + uri, payload=payload, requesttype=requestType)
    except:
        raise
        # return "%s REST API post failed..." % uri


def writeLog(updateItems, uri, httpAction, form, config):
    auditFile = config.get('files', 'auditfile')
    updateType = config.get('info', 'updatetype')
    try:
        username = form['userdata']
        username = username.username
    except:
        username = ''
    try:
        csvlogfh = csv.writer(codecs.open(auditFile, 'a', 'utf-8'), delimiter="\t")
        logrec = [httpAction, datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"), updateType, uri, username]
        for item in updateItems.keys():
            logrec.append("%s=%s" % (item, updateItems[item].replace('\n', '#')))
        csvlogfh.writerow(logrec)
    except:
        raise
        # html += 'writing to log %s failed!' % auditFile
        pass


def writeInfo2log(request, form, config, elapsedtime):
    action = str(form.get("action"))
    serverlabel = config.get('info', 'serverlabel')
    apptitle = config.get('info', 'apptitle')
    updateType = config.get('info', 'updatetype')
    institution = config.get('info', 'institution')
    checkServer = form.get('check')
    # override updateType if we are just checking the server
    if checkServer == 'check server':
        updateType = checkServer
    updateItems = {'app': apptitle, 'server': serverlabel, 'institution': institution,
                   'elapsedtime': '%8.2f' % elapsedtime, 'action': action}
    writeLog(updateItems, '', request, form, config)
