# -*- coding: utf-8 -*-
import csv
import sys
import re
import json
import logging
import requests
import urllib
from requests.auth import HTTPBasicAuth
from xml.etree.ElementTree import tostring, parse, Element, fromstring

import ConfigParser
from copy import deepcopy
from xml.sax.saxutils import escape

from common.unicode_hack import UnicodeReader, UnicodeWriter

import time
import urllib2

import re

reload(sys)
sys.setdefaultencoding('utf8')

sys.path.append("../../ucjeps")

from common import cspace  # we use the config file reading function
from cspace_django_site import settings
from os import path, listdir
from os.path import isfile, isdir, join
from common.Counter import Counter
from common.unicode_hack import UnicodeReader, UnicodeWriter

from extractOptions import get_lists
static_lists = get_lists(path.join(settings.BASE_PARENT_DIR, 'config/cspace-ui-config-ucjeps.json'))

# this hack provides a means to 'overlay' existing static lists with other lists.
# it is specifically implemented to allow the recoding of 'stateProvince' values for UCJEPS
with open(path.join(settings.BASE_PARENT_DIR, 'config/extra-lists.json'), 'rb') as e:
    extralists = e.read().encode('utf-8')
    e.close()
try:
    extra_static_lists = json.loads(extralists.replace('\n', ''))
except:
    print 'could not parse "extra-lists.json". aborting.'
    sys.exit(1)

config = cspace.getConfig(path.join(settings.BASE_PARENT_DIR, 'config'), 'csvimport')
TITLE = config.get('info', 'apptitle')
SERVERINFO = {
    'serverlabelcolor': config.get('info', 'serverlabelcolor'),
    'serverlabel': config.get('info', 'serverlabel')
}


IMPORTDIR = config.get('files', 'directory')
if isdir(IMPORTDIR):
    IMPORTDIR_MSG = "Using %s as working directory for csvimport files" % IMPORTDIR
else:
    IMPORTDIR_MSG =  "%s is not an existing directory, using /tmp instead for csvimport files" % IMPORTDIR
    QUEUEDIR = '/tmp'
    # raise Exception("csvImport working directory %s does not exist. this webapp will not work without it!" % QUEUEDIR)


MAPPING_FILE = []


class http_parms:
    pass


try:
    http_parms.realm = config.get('connect', 'realm')
    http_parms.hostname = config.get('connect', 'hostname')
    http_parms.port = config.get('connect', 'port')
    http_parms.protocol = config.get('connect', 'protocol')
    http_parms.username = config.get('connect', 'username')
    http_parms.password = config.get('connect', 'password')
    http_parms.institution = config.get('info', 'institution')

    http_parms.server = http_parms.protocol + "://" + http_parms.hostname
    try:
        int(http_parms.port)
        http_parms.server = http_parms.server + ':' + http_parms.port
    except:
        pass

except:
    print "could not get at least one of realm, hostname, port, protocol, username, password or institution from config file."
    # print "can't continue, exiting..."
    sys.exit(1)

def dump_row(row, error_type, message):
    MAPPING_FILE.append('%5s %-30s %-30s %-10s' % tuple(row[i] for i in [0, 1, 2, 4]) + '%-10s %s' % (error_type, message))

def load_mapping_file(mapping_file):
    mapping_file = path.join(path.join(settings.BASE_PARENT_DIR, 'config'), mapping_file)
    delim = '\t'
    cspace_mapping = {}
    constants = []
    dump_row('Row InputField CSpaceField X DataType X X'.split(' '), 'Status', 'Message')
    with open(mapping_file, 'r') as f1:
        reader = UnicodeReader(f1, delimiter=delim, quoting=csv.QUOTE_NONE, quotechar=chr(255))
        errors = 0
        for lineno, row in enumerate(reader):
            try:
                if row[1] != '' and row[1][0] == '#': continue
                if len(row) < 8:
                    dump_row(row, 'Error', 'not enough columns in this row')
                    errors += 1
                    continue
                row_id, input_field, cspace_field, additional_info, data_type, check_exists, authority, remarks = row[:8]
                if input_field == '' or cspace_field == '':
                    #dump_row(row, 'Warning', 'need both an input field name and a cspace field name')
                    continue
                #input_field = input_field.lower()
                if not data_type in 'constant static literal refname float integer date key'.split(' '):
                    dump_row(row, 'Error', 'unrecognized datatype: "%s"' % data_type)
                    errors += 1
                    continue
                if data_type == 'refname' and authority == '':
                    dump_row(row, 'Error', 'refname specified but no authority provided')
                    errors += 1
                    continue
                if data_type == 'constant':
                    constants.append([input_field, cspace_field, additional_info, data_type, check_exists, int(row_id), authority])
                # if the field already exists, make an 'alias' so it can be mapped multiple times
                if input_field in cspace_mapping:
                    cspace_mapping['=%s' % cspace_field] = [input_field, additional_info, data_type, check_exists, int(row_id), authority]
                else:
                    cspace_mapping[input_field] = [cspace_field, additional_info, data_type, check_exists, int(row_id), authority]
            except:
                dump_row(row, 'Error', 'unknown exception in mapping file')
                errors += 1
            dump_row(row, 'OK','')
    return cspace_mapping, errors, constants


def get_recordtypes():
    RECORDTYPES = config.get('info', 'recordtypes')
    try:
        RECORDTYPES = json.loads(RECORDTYPES.replace('\n', ''))
        for r in RECORDTYPES:
            RECORDTYPES[r].append(load_mapping_file(RECORDTYPES[r][1]))
    except:
        raise
        RECORDTYPES = {'configerror': ['Configuration Error', []]}
        print 'Error loading mapping file'
    return RECORDTYPES


# Get an instance of a logger, log some startup info
logger = logging.getLogger(__name__)


def get_import_file(filename):
    return path.join(IMPORTDIR, '%s') % filename


def getRecords(rawFile):
    rawFile.seek(0)
    delimiters = '\t ,'.split(' ')
    try:
        # see if the sniffer can figger out the csv dialect
        sample = rawFile.read(4096)
        dialect = csv.Sniffer().sniff(sample, delimiters = ',\t')
        rawFile.seek(0)
        csvfile = UnicodeReader(rawFile, dialect)
    except IOError, e:
        print "item%s " % e
        sys.exit(1)
    except:
        # nope, can't sniff: try a brute force approach, look for tabs, then commas...
        for delimiter in delimiters:
            if delimiter in sample:
                rawFile.seek(0)
                csvfile = UnicodeReader(rawFile, delimiter=delimiter)
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
    except IOError, e:
        print "item%s " % e
        sys.exit(1)
    except:
        raise


def check_file(file_handle):
    file_handle.seek(0)
    lines = file_handle.read().splitlines()
    recordtypes = [f.split("\t") for f in lines]
    return len(lines), recordtypes


# following function borrowed from Django docs, w modifications
def handle_uploaded_file(f):
    name_parts = f.name.split('.')
    extension = name_parts[-1]
    input_filename = f.name.replace('.%s' % extension, '.input.%s' % extension)
    destination = open(path.join(IMPORTDIR, '%s') % input_filename, 'wb+')
    with destination:
        for chunk in f.chunks():
            destination.write(chunk)
    destination.close()
    try:
        return getRecords(f)
    except:
        return None


def count_columns(matrix, header):
    types = {}
    for col in header:
        types[col] = Counter()
    column_count = len(header)
    for lineno, row in enumerate(matrix):
        for i, cell in enumerate(row):
            if cell != '':
                types[header[i]][cell] += 1

    stats = []
    for key in header:
        stats.append((key, len(types[key]), sum(types[key].values())))

    return stats, 'column types tokens'.split(' ')


def check_cell_in_cspace(mapping_key, key, value):
    if value == '':
        return 0, '', u''
    if mapping_key[2] == 'literal':
        return 0, 'a literal', value.decode('utf-8')
    elif mapping_key[2] == 'constant':
        return 0, 'a constant', mapping_key[5]
    elif mapping_key[2] == 'date':
        return 0, 'a date', value.decode('utf-8')
    elif mapping_key[2] == 'key':
        return 0, 'key', value
    elif mapping_key[2] == 'refname':
        refname = rest_query(value, '%s/items' % mapping_key[5])
        if refname[0] != 'OK':
            return 1, "refname for '%s' not found" % value, refname
        else:
            return 0, 'a refname', refname
    elif mapping_key[2] == 'static':
        if value in static_lists[mapping_key[5]]:
            return 0, 'a static value', ['OK', value, '', value]
        elif mapping_key[5] in extra_static_lists:
            if value in extra_static_lists[mapping_key[5]]:
                return 0, 'a static value', ['OK', value, '', extra_static_lists[mapping_key[5]][value]]
            else:
                return 1, "'%s' not found in 'extra' static list '%s'" % (value, mapping_key[5]), ['NotFoundExtra', value, '', '']
        else:
            return 1, "'%s' not found in static list '%s'" % (value, mapping_key[5]), ['NotFoundStatic', value, '', '']
        #return 1, 'static vocab terms not validated yet', 'NotValidated X X X X'.split(' ')
    elif mapping_key[2] == 'integer':
        try:
            int(value)
            return 0, 'an integer', unicode(int(value))
        except:
            return 1, '"%s" is not an integer. ' % value
    elif mapping_key[2] == 'float':
        try:
            float(value)
            return 0, 'a float', unicode(float(value))
        except:
            return 1, '"%s" is not a float. ' % value
    else:
        return 0, 'unvalidated', value.decode('utf-8')


def validate_cell(CSPACE_MAPPING, key, values):
    max_problems_to_log = 4
    num_problems = 0
    messages = []
    validated_values = {}
    if key in CSPACE_MAPPING:
        for v in values:
            try:
                isaproblem, message, validated_value = check_cell_in_cspace(CSPACE_MAPPING[key], key, v)
            except:
                print "problem key", key
                print "problem value", v
                print "mapping", CSPACE_MAPPING[key]
                isaproblem, message, validated_value = 1, 'exception', v
            validated_values[v] = validated_value
            num_problems += isaproblem
            if isaproblem != 0:
                if num_problems > max_problems_to_log:
                    continue
                else:
                    messages.append(message)
        if num_problems > max_problems_to_log:
            messages.append('[... and %s more.]' % num_problems)
    else:
        messages = ['column ignored: not a mapped field']
    valid_label = 'OK' if num_problems == 0 else 'Not OK'
    return valid_label, num_problems, '; '.join(messages), validated_values


def map2cspace(CSPACE_MAPPING, cell, j, stats, header):
    stat = stats[0][j]
    value_dict = stat[7]
    result = cell
    OK = 0
    if cell in value_dict:
        if type(value_dict[cell]) == type([]):
            if value_dict[cell][0] == 'OK':
                result = value_dict[cell][3]
            else:
                OK = 1
                result = ''
        else:
            result = value_dict[cell]
    return OK, result


def validate_columns(CSPACE_MAPPING, matrix, header, in_progress):
    types = {}
    for col in header:
        types[col] = Counter()
    column_count = len(header)
    for lineno, row in enumerate(matrix):
        for i, cell in enumerate(row):
            if cell != '':
                types[header[i]][cell] += 1

    stats = []
    for key in header:
        in_progress.write("column %s (%s values) validation started at %s\n" % (key, len(types[key]), time.strftime("%b %d %Y %H:%M:%S", time.localtime())))
        in_progress.flush()
        valid_label, num_problems, message, validated_values = validate_cell(CSPACE_MAPPING, key, types[key])
        stats.append([key, len(types[key]), sum(types[key].values()), valid_label, num_problems, message, types[key], validated_values])

    # filter out columns that have no data.
    #stats = [s for s in stats if s[1] > 0]
    return stats, 'column types tokens status problems messages types valid_values'.split(' ')


def map_items(input_data, file_header):
    data_dict = {}
    for i,cell in enumerate(input_data):
        data_dict[file_header[i]] = cell
    return data_dict


def validate_items(CSPACE_MAPPING, constants, input_data, file_header, uri, in_progress, action):
    stats = validate_columns(CSPACE_MAPPING, input_data, file_header, in_progress)

    keyrow = -1
    try:
        for field in CSPACE_MAPPING:
            if CSPACE_MAPPING[field][2] == 'key':
                keyfield = field
                keyrow = file_header.index(keyfield)
                break
    except:
        pass

    validated_items = []
    nonvalidating_items = []
    for i,row in enumerate(input_data):
        output_row = []
        validated = 0
        for j,cell in enumerate(row):
            validation_status, mapped_row = map2cspace(CSPACE_MAPPING,cell, j, stats, file_header)
            validated += validation_status
            output_row.append(mapped_row)
        output_row += extract_constants(constants, row, file_header)
        if validated == 0:
            validated_items.append(output_row)
        else:
            nonvalidating_items.append(row)
    number_check = check_key(stats[0][keyrow][7], action, uri, in_progress)
    return validated_items, nonvalidating_items, stats, number_check, keyrow


def extract_constants(constants, row, file_header):
    constant_field_values = []
    for fld in constants:
        assoc_field_name = fld[4]
        constant_value = fld[2]
        if assoc_field_name == '':
            constant_field_value = constant_value
        else:
            constant_field_value = ''
            if assoc_field_name in file_header:
                constant_field_index = file_header.index(assoc_field_name)
                if row[constant_field_index] != '':
                    constant_field_value = constant_value
        constant_field_values.append(constant_field_value)
    return constant_field_values

def check_key(key_dict, action, uri, in_progress):
    for recordsprocessed, k in enumerate(key_dict):
        refname = rest_query(k, uri)
        if recordsprocessed % 1000 == 0:
            in_progress.write("%s keys checked of %s, %s\n" % (recordsprocessed, len(key_dict.keys()), time.strftime("%b %d %Y %H:%M:%S", time.localtime())))
            in_progress.flush()
        if refname[0] != 'ZeroResults':
            key_dict[k] = refname[1]
        else:
            key_dict[k] = ''
    return key_dict

def check_columns(labels, header, field_map):
    RECORDTYPES = get_recordtypes()
    cspace_fields = RECORDTYPES[field_map][2]
    handling = []
    if header == 'use':
        for label in labels:
            try:
                cspace_field = [cspace_fields[i] for i in cspace_fields if i == label]
                handling += cspace_field
            except:
                handling.append(None)
    elif header == 'ignore':
        pass
    elif header == 'none':
        pass
    return handling


def loginfo(infotype, line, request):
    logdata = ''
    # user = getattr(request, 'user', None)
    if request.user and not request.user.is_anonymous():
        username = request.user.username
    else:
        username = '-'
    logger.info('%s :: %s :: %s' % (infotype, line, logdata))


def extract_tag(xml, tag):
    element = xml.find('.//%s' % tag)
    return element.text

def normalize(term):
    return re.sub(r"[\&\.\-')(/, ]+",' ', term).replace(' and ',' ').strip().upper()


def extract_refname(xml, term, pgSz):
    try:
        cspaceXML = fromstring(xml)
        totalItems = int(cspaceXML.find('.//totalItems').text)
        if totalItems == 0:
            return 'ZeroResults X X X X'.split(' '), totalItems
        items = cspaceXML.findall('.//list-item')
        for i in items:
            csid = i.find('.//csid')
            csid = csid.text
            try:
                refName = extract_tag(i, 'refName')
                updated_at = extract_tag(i, 'updatedAt')
                try:
                    termDisplayName = extract_tag(i, 'termDisplayName')
                except:
                    try:
                        termDisplayName = extract_tag(i, 'displayName')
                    except:
                        return ['NoDisplayName', csid, '', refName, updated_at], totalItems
            except:
                print 'could not get termDisplayName or refName or updatedAt from %s' % csid
                return 'Failed X X X X'.split(' '), totalItems
            if normalize(term.encode('utf-8')) == normalize(termDisplayName.encode('utf-8')):
                return ['OK', csid, unicode(termDisplayName), refName, updated_at], totalItems
        if totalItems > pgSz:
            return 'MaybeMissed X X X X'.split(' '), totalItems
        return 'NoMatch X X X X'.split(' '), totalItems
    except:
        raise
        return 'Failed X X X X'.split(' '), totalItems


def rest_query(term, record_type):
    pgSz = 100
    search_term = normalize(term.encode('utf-8'))
    response = do_query('kw', search_term, record_type, pgSz)
    if response.status_code != 200:
        error_msg = "HTTP%s X X X X" % response.status_code
        return error_msg.split(' ')
    refname_result, totalitems = extract_refname(response.content, term, pgSz)
    if totalitems > pgSz:
        print '%s term %s (=%s) returned %s for kw search, only %s examined. status is %s.' % (record_type, term.encode('utf-8'), search_term, totalitems, pgSz, refname_result[0])
    # hail mary: do a pt search if kw fails
    if refname_result[0] != 'OK' and refname_result[0] != 'ZeroResults':
        print 'fallback: %s term (=%s) %s trying pt search.' % (record_type, term.encode('utf-8'), search_term)
        response = do_query('pt', term, record_type, pgSz)
        refname_result, totalitems = extract_refname(response.content, term, pgSz)
        if totalitems > pgSz:
            print '% term %s returned %s for pt search, only %s examined. status is %s.' % (record_type, term, totalitems, pgSz, refname_result[0])
        if response.status_code != 200:
            error_msg = "HTTP%s X X X X" % response.status_code
            return error_msg.split(' ')
        if refname_result[0] != 'OK':
            print 'fallback for %s worked!' % term
    return refname_result


def do_query(index, search_term, record_type, pgSz):
    querystring = {index: search_term, 'wf_deleted': 'false', 'pgSz': pgSz}
    querystring = urllib.urlencode(querystring)
    # print querystring
    url = '%s/cspace-services/%s?%s' % (http_parms.server, record_type, querystring)
    response = requests.get(url, auth=HTTPBasicAuth(http_parms.username, http_parms.password))
    # response.raise_for_status()

    response.encoding = 'utf-8'
    return response


def count_numbers(number_check):
    found = 0
    not_found = 0
    total = 0
    for key in number_check:
        if number_check[key] == '':
            not_found += 1
        else:
            found += 1
        total += 1

    return not_found, found, total

def count_stats(stats, mapping):
    ok_count = 0
    bad_count = 0
    bad_values = 0
    print
    print '%-35s %10s %10s  %-10s %10s' % tuple(stats[1][:5])
    print
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
                    if s[0] in mapping:
                        if mapping[s[0]][2] == 'refname' or mapping[s[0]][2] == 'static':
                            label = items[item_key][0]
                        else:
                            label = 'invalid value:'
                    print '  %15s: %s' % (label, item_key.encode('utf-8'))
                    bad_values += 1

    return ok_count, bad_count, bad_values

def write_intermediate_files(stats, validated_data, nonvalidating_items, constants, file_header, mapping, outputfh, nonvalidfh, termsfh, number_check, keyrow):

    successes = 0
    failures = 0
    recordsprocessed = 0

    for s in stats[0]:
        if 'column ignored' in s[5]:
            continue
        term_row = [str(x) for x in s[:5]]
        for i, t in enumerate(s[6]):
            term_extra = (t, str(s[6][t]))
            if t in s[7].keys() and type(s[7][t]) == type([]):
                term_extra += tuple(s[7][t])
            else:
                term_extra += ('OK', s[7][t], '', '', '')
            termsfh.writerow(tuple(term_row) + term_extra)

    cspace_header = ['csid']
    for h in file_header:
        if h in mapping:
            cspace_header.append(mapping[h][0])
        else:
            cspace_header.append('unmapped')

    outputfh.writerow(cspace_header + [c[0] for c in constants])
    outputfh.writerow(['csid'] + file_header + [c[0] for c in constants])
    for input_data in validated_data:
        try:
            outputfh.writerow([number_check[input_data[keyrow]]] + input_data)
            recordsprocessed += 1
            successes += 1
        except:
            outputfh.writerow([''] + input_data)
            recordsprocessed += 1
            successes += 1

    nonvalidfh.writerow(['csid'] + file_header)
    for input_data in nonvalidating_items:
        try:
            nonvalidfh.writerow([number_check[input_data[keyrow]]] + input_data)
            recordsprocessed += 1
            failures += 1
        except:
            outputfh.writerow([''] + input_data)
            recordsprocessed += 1
            failures += 1
            # try:
            #    print 'could not write: ', number_check[input_data[keyrow]]
            # except:
            #    pass

    return recordsprocessed, successes, failures

def send_to_cspace(action, inputRecords, file_header, xmlTemplate, outputfh, uri, in_progress):
    recordsprocessed = 0
    successes = 0
    for input_data in inputRecords:

        if recordsprocessed % 1000 == 0:
            in_progress.write("%s records of %s output %s\n" % (recordsprocessed, len(inputRecords), time.strftime("%b %d %Y %H:%M:%S", time.localtime())))
            in_progress.flush()

        cspaceElements = ['', '']
        elapsedtimetotal = time.time()
        try:
            input_dict = map_items(input_data, file_header)
            cspaceElements = DWC2CSPACE(action, xmlTemplate, input_dict, config, uri)
            del cspaceElements[2]
            cspaceElements.append('%8.2f' % (time.time() - elapsedtimetotal))
            print "itemitem: %s, csid: %s %s" % tuple(cspaceElements)
            if cspaceElements[1] != '':
                successes += 1
            outputfh.writerow(cspaceElements)
            # flush output buffers so we get a much data as possible if there is a failure
            outputfh.flush()
            sys.stdout.flush()
        except:
            print "item create failed for objectnumber %s, %8.2f" % (
            cspaceElements, (time.time() - elapsedtimetotal))
            raise
        recordsprocessed += 1
    return recordsprocessed, successes


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
    request = urllib2.Request(url, payload.encode('utf-8'), {'Content-Type': 'application/xml'})
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
        #print payload
        #print data
        if info: print info
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


def DWC2CSPACE(action, xmlTemplate, input_dataDict, config, uri):
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

    messages = []
    try:
        itemNumber = input_dataDict['key']
    except:
        itemNumber = ''
        messages.append('could not find an item key')
        #return ['', '', messages]

    if action == 'add':
        messages.append("POSTing (add) to cspace REST API...")
        payload = createXMLpayload(xmlTemplate, input_dataDict, INSTITUTION)
    elif action == 'update':
        messages.append("PUTting (update) to cspace REST API...")
        itemCSID = input_dataDict['csid']
        url = '%s/cspace-services/%s/%s' % (http_parms.server, uri, itemCSID)
        try:
            response = requests.get(url, auth=HTTPBasicAuth(http_parms.username, http_parms.password))
            payload = response.content
            if response.status_code != 200:
                messages.append("HTTP %s" % response.status_code)
            else:
                (url, data, dummyCSID, elapsedtime) = postxml('PUT', '%s/%s' % (uri, itemCSID), realm, protocol, hostname, port, username, password, payload)
                pass
        except:
            itemCSID = ''
            messages.append("cspace REST API put failed...")
        #payload = createXMLpayload(xmlTemplate, input_dataDict, INSTITUTION)
    try:
        (url, data, itemCSID, elapsedtime) = postxml('POST', uri, realm, protocol, hostname, port, username, password, payload)
        messages.append('got cspacecsid %s elapsedtime %s ' % (itemCSID, elapsedtime))
        messages.append("cspace REST API post succeeded...")
    except:
        itemCSID = ''
        messages.append("cspace REST API post failed...")

    return [itemNumber, itemCSID, messages]
