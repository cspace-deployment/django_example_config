import csv
import sys
import codecs
import time

# NB: the BMU facility uses methods from the "legacy" CGI webapps, imported below.
# Therefore, it must either be run from the directory where these modules live,
# or these modules must be copied to where the batch system (i.e. cron job) runs the script
#
# at the moment, the whole shebang expects to be run in /var/www/cgi-bin, and there are
# a couple of hardcoded dependencies below

CONFIGDIRECTORY = '/var/www/cfgs/'

from cswaUtils import postxml, relationsPayload, getConfig
from cswaDB import getCSID


def tricoderPayload(f, institution):
    payload = """<?xml version="1.0" encoding="UTF-8"?>
<document name="tricoder">
<ns2:tricoder_common xmlns:ns2="http://collectionspace.org/services/tricoder" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
<blobCsid>%s</blobCsid>
<rightsHolder>%s</rightsHolder>
<creator>%s</creator>
<title>%s</title>
<description>%s</description>
<languageList>
<language>urn:cspace:INSTITUTION.cspace.berkeley.edu:vocabularies:name(languages):item:name(eng)'English'</language>
</languageList>
<identificationNumber>%s</identificationNumber>
</ns2:tricoder_common>
<ns2:tricoder_INSTITUTION xmlns:ns2="http://collectionspace.org/services/tricoder/local/INSTITUTION" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
<approvedForWeb>true</approvedForWeb>
<primaryDisplay>false</primaryDisplay>
IMAGENUMBERELEMENT
</ns2:tricoder_INSTITUTION>
</document>
"""
    if institution == 'bampfa':
        payload = payload.replace('IMAGENUMBERELEMENT', '<imageNumber>%s</imageNumber>' % f['imageNumber'])
    else:
        payload = payload.replace('IMAGENUMBERELEMENT', '')
    payload = payload.replace('INSTITUTION', institution)
    payload = payload % (
        f['blobCsid'], f['rightsHolderRefname'], f['creator'], f['name'], f['contributor'], f['objectNumber'])
    # print payload
    return payload


def uploadtricoder(tricoderElements, config):
    try:
        realm = config.get('connect', 'realm')
        hostname = config.get('connect', 'hostname')
        username = config.get('connect', 'username')
        password = config.get('connect', 'password')
        INSTITUTION = config.get('info', 'institution')
    except:
        print "could not get at least one of realm, hostname, username, password or institution from config file."
        # print "can't continue, exiting..."
        raise

    objectCSID = getCSID('objectnumber', tricoderElements['objectnumber'], config)
    if objectCSID == [] or objectCSID is None:
        print "could not get (i.e. find) objectnumber's csid: %s." % tricoderElements['objectnumber']
        # raise Exception("<span style='color:red'>Object Number not found: %s!</span>" % tricoderElements['objectnumber'])
        #raise
    else:
        objectCSID = objectCSID[0]
        tricoderElements['objectCSID'] = objectCSID

        updateItems = {'objectStatus': 'found',
                       'subjectCsid': '',
                       'objectCsid': tricoderElements['objectCSID'],
                       'objectNumber': tricoderElements['objectnumber'],
                       'imageNumber': tricoderElements['imagenumber'],
                       'blobCsid': tricoderElements['blobCSID'],
                       'name': tricoderElements['name'],
                       'rightsHolderRefname': tricoderElements['rightsholder'],
                       'contributor': tricoderElements['contributor'],
                       'creator': tricoderElements['creator'],
                       'tricoderDate': tricoderElements['date'],
        }

        uri = 'tricoder'

        messages = []
        messages.append("posting to tricoder REST API...")
        # print updateItems
        payload = tricoderPayload(updateItems, INSTITUTION)
        messages.append(payload)
        messages.append(payload)
        (url, data, tricoderCSID, elapsedtime) = postxml('POST', uri, realm, hostname, username, password, payload)
        #elapsedtimetotal += elapsedtime
        messages.append('got tricodercsid %s elapsedtime %s ' % (tricoderCSID, elapsedtime))
        tricoderElements['tricoderCSID'] = tricoderCSID
        messages.append("tricoder REST API post succeeded...")

        # now relate tricoder record to collection object

        uri = 'relations'

        messages.append("posting tricoder2obj to relations REST API...")

        updateItems['objectCsid'] = objectCSID
        updateItems['subjectCsid'] = tricoderCSID
        # "urn:cspace:INSTITUTION.cspace.berkeley.edu:tricoder:id(%s)" % tricoderCSID

        updateItems['objectDocumentType'] = 'CollectionObject'
        updateItems['subjectDocumentType'] = 'Media'

        payload = relationsPayload(updateItems)
        (url, data, csid, elapsedtime) = postxml('POST', uri, realm, hostname, username, password, payload)
        #elapsedtimetotal += elapsedtime
        messages.append('got relation csid %s elapsedtime %s ' % (csid, elapsedtime))
        tricoderElements['tricoder2objCSID'] = csid
        messages.append("relations REST API post succeeded...")

        # reverse the roles
        messages.append("posting obj2tricoder to relations REST API...")
        temp = updateItems['objectCsid']
        updateItems['objectCsid'] = updateItems['subjectCsid']
        updateItems['subjectCsid'] = temp
        updateItems['objectDocumentType'] = 'Media'
        updateItems['subjectDocumentType'] = 'CollectionObject'
        payload = relationsPayload(updateItems)
        (url, data, csid, elapsedtime) = postxml('POST', uri, realm, hostname, username, password, payload)
        #elapsedtimetotal += elapsedtime
        messages.append('got relation csid %s elapsedtime %s ' % (csid, elapsedtime))
        tricoderElements['obj2tricoderCSID'] = csid
        messages.append("relations REST API post succeeded...")

    return tricoderElements


class CleanlinesFile(file):
    def next(self):
        line = super(CleanlinesFile, self).next()
        return line.replace('\r', '').replace('\n', '') + '\n'


def getRecords(rawFile):
    # csvfile = csv.reader(codecs.open(rawFile,'rb','utf-8'),delimiter="\t")
    try:
        f = CleanlinesFile(rawFile, 'rb')
        csvfile = csv.reader(f, delimiter="|")
    except IOError:
        message = 'Expected to be able to read %s, but it was not found or unreadable' % rawFile
        return message, -1
    except:
        raise

    try:
        records = []
        for row, values in enumerate(csvfile):
            records.append(values)
        return records, len(values)
    except IOError:
        message = 'Could not read (or maybe parse) rows from %s' % rawFile
        return message, -1
    except:
        raise


if __name__ == "__main__":

    print "MEDIA: config file: %s" % sys.argv[2]
    print "MEDIA: input  file: %s" % sys.argv[1]

    try:
        form = {'webapp': CONFIGDIRECTORY + sys.argv[2]}
        config = getConfig(form)
    except:
        print "MEDIA: could not get configuration"
        sys.exit()

    # print 'config',config
    records, columns = getRecords(sys.argv[1])
    if columns == -1:
        print 'MEDIA: Error! %s' % records
        sys.exit()

    print 'MEDIA: %s columns and %s lines found in file %s' % (columns, len(records), sys.argv[1])
    outputFile = sys.argv[1].replace('.step2.csv', '.step3.csv')
    outputfh = csv.writer(open(outputFile, 'wb'), delimiter="\t")

    for i, r in enumerate(records):

        elapsedtimetotal = time.time()
        tricoderElements = {}
        for v1, v2 in enumerate(
                'name size objectnumber blobCSID date creator contributor rightsholder imagenumber filenamewithpath'.split(' ')):
            tricoderElements[v2] = r[v1]
        #print tricoderElements
        print 'objectnumber %s' % tricoderElements['objectnumber']
        try:
            tricoderElements = uploadtricoder(tricoderElements, config)
            print "MEDIA: objectnumber %s, objectcsid: %s, tricodercsid: %s, %8.2f" % (
                tricoderElements['objectnumber'], tricoderElements['objectCSID'], tricoderElements['tricoderCSID'], (time.time() - elapsedtimetotal))
            r.append(tricoderElements['tricoderCSID'])
            r.append(tricoderElements['objectCSID'])
            outputfh.writerow(r)
        except:
            print "MEDIA: create failed for objectnumber %s, %8.2f" % (
                tricoderElements['objectnumber'], (time.time() - elapsedtimetotal))
            # raise

