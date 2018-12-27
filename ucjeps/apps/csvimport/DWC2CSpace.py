import csv
import sys
import ConfigParser
from copy import deepcopy
from xml.sax.saxutils import escape

import time
import urllib2

import re

from utils import load_mapping_file, validate_columns, map2cspace, count_columns, dump_row

CONFIGDIRECTORY = ''


def getConfig(fileName):
    try:
        config = ConfigParser.RawConfigParser()
        config.read(fileName)
        # test to see if it seems like it is really a config file
        connect = config.get('connect', 'hostname')
        return config
    except:
        return False


def postxml(requestType, uri, realm, protocol, hostname, port, username, password, payload):
    data = None
    csid = ''

    if port != '':
        port = ':' + port
    server = protocol + "://" + hostname + port
    passman = urllib2.HTTPPasswordMgr()
    passman.add_password(realm, server, username, password)
    authhandler = urllib2.HTTPBasicAuthHandler(passman)
    opener = urllib2.build_opener(authhandler)
    urllib2.install_opener(opener)
    url = "%s/cspace-services/%s" % (server, uri)

    elapsedtime = time.time()
    request = urllib2.Request(url, payload, {'Content-Type': 'application/xml'})
    # default method for urllib2 with payload is POST
    if requestType == 'PUT': request.get_method = lambda: 'PUT'
    try:
        f = urllib2.urlopen(request)
        data = f.read()
        info = f.info()
        # if a POST, the Location element contains the new CSID
        if info.getheader('Location'):
            csid = re.search(uri + '/(.*)', info.getheader('Location')).group(1)
        else:
            csid = ''
    except urllib2.HTTPError, e:
        sys.stderr.write('URL: ' + url + '\n')
        sys.stderr.write('PUT failed, HTTP code: ' + str(e.code) + '\n')
        print payload
        print data
        print info
        sys.stderr.write('Data: ' + data + '\n')
        raise
    except urllib2.URLError, e:
        sys.stderr.write('URL: ' + url + '\n')
        if hasattr(e, 'reason'):
            sys.stderr.write('We failed to reach a server.\n')
            sys.stderr.write('Reason: ' + str(e.reason) + '\n')
        if hasattr(e, 'code'):
            sys.stderr.write('The server couldn\'t fulfill the request.\n')
            sys.stderr.write('Error code: ' + str(e.code) + '\n')
        if True:
            # print 'Error in POSTing!'
            sys.stderr.write("Error in POSTing!\n")
            sys.stderr.write(payload)
            raise
    except:
        sys.stderr.write('Some other error' + '\n')
        raise

    elapsedtime = time.time() - elapsedtime
    return (url, data, csid, elapsedtime)


def createXMLpayload(template, values, institution):
    payload = deepcopy(template)
    for v in values.keys():
        payload = payload.replace('{' + v + '}', escape(values[v]))
    # get rid of remaining unsubstituted template variables
    payload = re.sub('(<.*?>){(.*)}(<.*>)', r'\1\3', payload)
    return payload


def DWC2CSPACE(xmlTemplate, input_dataDict, config):
    try:
        realm = config.get('connect', 'realm')
        hostname = config.get('connect', 'hostname')
        port = config.get('connect', 'port')
        protocol = config.get('connect', 'protocol')
        username = config.get('connect', 'username')
        password = config.get('connect', 'password')
        INSTITUTION = config.get('info', 'institution')
    except:
        print "could not get at least one of realm, hostname, username, password or institution from config file."
        # print "can't continue, exiting..."
        raise

    # objectCSID = getCSID('objectnumber', cspaceElements['objectnumber'], config)
    messages = []
    try:
        objectNumber = input_dataDict['catalogNumber']
    except:
        messages.append('could not find an accession number')
        return ['', '', messages]

    uri = 'collectionobjects'

    messages.append("posting to cspace REST API...")
    payload = createXMLpayload(xmlTemplate, input_dataDict, INSTITUTION)
    # print payload
    (url, data, objectCSID, elapsedtime) = postxml('POST', uri, realm, protocol, hostname, port, username, password, payload)
    messages.append('got cspacecsid %s elapsedtime %s ' % (objectCSID, elapsedtime))
    messages.append("cspace REST API post succeeded...")

    return [objectNumber, objectCSID, messages]


class CleanlinesFile(file):
    def next(self):
        line = super(CleanlinesFile, self).next()
        return line.replace('\r', '').replace('\n', '') + '\n'


def getRecords(rawFile):
    # csvfile = csv.reader(codecs.open(rawFile,'rb','utf-8'),delimiter="\t")
    delimiters = '\t ,'.split(' ')
    try:
        f = CleanlinesFile(rawFile, 'rb')
        # see if the sniffer can figger out the csv dialect
        sample = f.read(2048)
        dialect = csv.Sniffer().sniff(sample, delimiters = ',\t')
        f.seek(0)
        csvfile = csv.reader(f, dialect)
    except IOError:
        message = 'Expected to be able to read %s, but it was not found or unreadable' % rawFile
        return message, -1
    except:
        for delimiter in delimiters:
            if delimiter in sample:
                f.seek(0)
                csvfile = csv.reader(f, delimiter=delimiter)
                break

    try:
        rows = []
        cell_values = {}
        for rowNumber, row in enumerate(csvfile):
            if rowNumber == 0:
                header = row
                continue
            rows.append(row)
            for col_number, cell in enumerate(row):
                if cell == "#": continue  # skip comments
                col_name = header[col_number]
                cell_values.setdefault(col_name, {})
                if not row[col_number] in cell_values[col_name]:
                    cell_values[col_name][row[col_number]] = 0
                    #cell_values[col_name]['bcid'] = row[0]
                cell_values[col_name][row[col_number]] += 1
        return cell_values, rows, rowNumber, header
    except IOError:
        raise
        message = 'could not read (or maybe parse) rows from %s' % rawFile
        return message, -1
    except:
        raise


def map_items(input_data, file_header):
    data_dict = {}
    for i,cell in enumerate(input_data):
        data_dict[file_header[i]] = cell
    return data_dict


def validate_items(CSPACE_MAPPING, input_data, file_header):
    stats = validate_columns(CSPACE_MAPPING, input_data, file_header)
    validated_items = []
    for i,row in enumerate(input_data):
        output_row = []
        for j,cell in enumerate(row):
            output_row.append(map2cspace(CSPACE_MAPPING,cell, j, stats, file_header))
        validated_items.append(output_row)
    return validated_items, stats

def main():

    header = "*" * 100

    if len(sys.argv) < 7:
        print('%s <csv input file> <config file> <mapping file> <template> <output file> <action>') % sys.argv[0]
        sys.exit()

    print header
    print "DWC2CSPACE: input  file:    %s" % sys.argv[1]
    print "DWC2CSPACE: config file:    %s" % sys.argv[2]
    print "DWC2CSPACE: mapping file:   %s" % sys.argv[3]
    print "DWC2CSPACE: template:       %s" % sys.argv[4]
    print "DWC2CSPACE: output file:    %s" % sys.argv[5]
    print "DWC2CSPACE: action:         %s" % sys.argv[6]
    print header


    try:
        action = sys.argv[6]
        actions = 'count validate add update both'
        if not action in actions.split(' '):
            print 'DWC2CSPACE: Error! not a valid action: %s' % action
            sys.exit()
    except:
        print "DWC2CSPACE: action could not be understood: should be one of: %s" % actions
        sys.exit()

    try:
        dataDict, inputRecords, lines, file_header = getRecords(sys.argv[1])
        print 'DWC2CSPACE: %s lines and %s records found in file %s' % (lines, len(inputRecords), sys.argv[1])
        print header
        if lines == -1:
            print 'DWC2CSPACE: Error! %s' % inputRecords
            sys.exit()
    except:
        raise
        print "DWC2CSPACE: could not get CSV records to load"
        sys.exit()

    try:
        config = getConfig(sys.argv[2])
        print "DWC2CSPACE: hostname        %s" % config.get('connect', 'hostname')
        print "DWC2CSPACE: institution     %s" % config.get('info', 'institution')
        print header
    except:
        print "DWC2CSPACE: could not get cspace server configuration"
        sys.exit()

    try:
        print "DWC2CSPACE: loading mapping file %s\n" % sys.argv[3]
        mapping, errors = load_mapping_file(sys.argv[3])
        print '\nDWC2CSPACE: %s valid records found in mapping file %s' % (len(mapping), sys.argv[3])
        # print mapping
        print header
        if errors != 0:
            print "DWC2CSPACE: terminating due to %s errors detected in mapping configuration" % errors
            sys.exit()
    except:
        print "DWC2CSPACE: could not get mapping configuration"
        sys.exit()

    try:
        with open(sys.argv[4], 'rb') as f:
            xmlTemplate = f.read()
            # print xmlTemplate
    except:
        print "DWC2CSPACE: could not get template"
        sys.exit()

    try:
        outputfh = csv.writer(open(sys.argv[5], 'wb'), delimiter="\t")
    except:
        print "DWC2CSPACE: could not open output file for write %s" % sys.argv[5]
        sys.exit()

    successes = 0
    recordsprocessed = 0


    if action == 'count':
        stats = count_columns(inputRecords, file_header)
        print '%-35s %10s %10s' % tuple(stats[1])
        print
        for s in stats[0]:
            print '%-35s %10s %10s' % tuple(s)
        print
        recordsprocessed = len(inputRecords)
        successes = len(inputRecords)

    elif action == 'validate':
        validated_data, stats = validate_items(mapping, inputRecords, file_header)
        ok_count = 0
        bad_count = 0
        bad_values = 0
        print '%-35s %10s %10s  %-10s %10s' % tuple(stats[1][:5])
        for s in stats[0]:
            if s[3] == 'OK':
                ok_count += 1
                print '%-35s %10s %10s  %-10s %10s' % tuple(s[:5])
            else:
                bad_count += 1
                print '%-35s %10s %10s  %-10s %10s' % tuple(s[:5])
                items = s[7]
                for item_key in sorted(items):
                    if items[item_key][0] != 'OK':
                        print '%15s: %s' % (items[item_key][0], item_key)
                        bad_values += 1
        if bad_count != 0:
            print "DWC2CSPACE: validation failed (%s fields had %s values in error)" % (bad_count, bad_values)
            print "DWC2CSPACE: cowardly refusal to write invalid output file"
            sys.exit(1)

        outputfh.writerow(file_header)
        for input_data in validated_data:
            outputfh.writerow(input_data)
            recordsprocessed += 1
            successes += 1

    for input_data in inputRecords:

        if action == 'add':

            cspaceElements = ['', '']
            elapsedtimetotal = time.time()
            try:
                input_dict = map_items(input_data, file_header)
                cspaceElements = DWC2CSPACE(xmlTemplate, input_dict, config)
                del cspaceElements[2]
                cspaceElements.append(time.time() - elapsedtimetotal)
                print "DWC2CSPACE: objectnumber: %s, objectcsid: %s %8.2f" % tuple(cspaceElements)
                if cspaceElements[1] != '':
                    successes += 1
                outputfh.writerow(cspaceElements)
            except:
                print "DWC2CSPACE: create failed for objectnumber %s, %8.2f" % (cspaceElements, (time.time() - elapsedtimetotal))
                raise
            recordsprocessed += 1

        elif action == 'update':

            cspaceElements = ['', '']
            elapsedtimetotal = time.time()
            try:
                input_dict = map_items(input_data, file_header)
                cspaceElements = DWC2CSPACE(xmlTemplate, input_dict, config)
                del cspaceElements[2]
                cspaceElements.append(time.time() - elapsedtimetotal)
                print "DWC2CSPACE: objectnumber: %s, objectcsid: %s %8.2f" % tuple(cspaceElements)
                if cspaceElements[1] != '':
                    successes += 1
                outputfh.writerow(cspaceElements)
            except:
                print "DWC2CSPACE: create failed for objectnumber %s, %8.2f" % (
                cspaceElements, (time.time() - elapsedtimetotal))
                raise
            recordsprocessed += 1

    print "DWC2CSPACE: %s records. %s processed, %s successful" % (action, recordsprocessed, successes)
    print header

if __name__ == "__main__":
    main()