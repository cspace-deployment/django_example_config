import csv
import sys
import json
import logging
import requests
import urllib
from requests.auth import HTTPBasicAuth
from xml.etree.ElementTree import tostring, parse, Element, fromstring

sys.path.append("/Users/jblowe/PyCharmProjects/ucjeps")

from common import cspace  # we use the config file reading function
from cspace_django_site import settings
from os import path, listdir
from os.path import isfile, isdir, join
from common.Counter import Counter
from common.unicode_hack import UnicodeReader, UnicodeWriter

config = cspace.getConfig(path.join(settings.BASE_PARENT_DIR, 'config'), 'csvimport')
TITLE = config.get('info', 'apptitle')
SERVERINFO = {
    'serverlabelcolor': config.get('info', 'serverlabelcolor'),
    'serverlabel': config.get('info', 'serverlabel')
}


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
    print '%5s %-30s %-30s %-10s' % tuple(row[i] for i in [0, 1, 2, 4]),
    print '%-10s %s' % (error_type, message)


def load_mapping_file(mapping_file):
    mapping_file = path.join(path.join(settings.BASE_PARENT_DIR, 'config'), mapping_file)
    delim = '\t'
    cspace_mapping = {}
    dump_row('Row InputField CSpaceField X DataType X X'.split(' '), 'Status', 'Message')
    print
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
                # id * FIMS field name * Cspace collectionobject tag * context tag * data type * check exists? * authority * csid
                row_id, input_field, cspace_field, context_tag, data_type, check_exists, authority, remarks = row[:8]
                if input_field == '' or cspace_field == '':
                    #dump_row(row, 'Warning', 'need both an input field name and a cspace field name')
                    continue
                #input_field = input_field.lower()
                if data_type == 'refname' and authority == '':
                    dump_row(row, 'Error', 'refname specified but no authority provided')
                    errors += 1
                    continue
                if not data_type in 'static literal refname float integer date key'.split(' '):
                    dump_row(row, 'Error', 'unrecognized datatype: %s' % data_type)
                    errors += 1
                    continue
                cspace_mapping[input_field] = [cspace_field, context_tag, data_type, check_exists, int(row_id), authority]
            except:
                dump_row(row, 'Error', 'unknown exception in mapping file')
                errors += 1
            dump_row(row, 'OK','')
    return cspace_mapping, errors

online = False
if online is True:
    RECORDTYPES = config.get('info', 'recordtypes')
    try:
        RECORDTYPES = json.loads(RECORDTYPES.replace('\n', ''))
        for r in RECORDTYPES:
            RECORDTYPES[r].append(load_mapping_file(RECORDTYPES[r][1]))
    except:
        raise
        RECORDTYPES = {'configerror': ['Configuration Error', []]}
        print 'Error loading mapping file'

IMPORTDIR = config.get('files', 'directory')
if isdir(IMPORTDIR):
    print "Using %s as working directory for import files and metadata files" % (IMPORTDIR)
else:
    print "Working directory %s does not exist. this webapp will not work!" % (IMPORTDIR)
    print "Using /tmp as a placeholder"
    IMPORTDIR = "/tmp"



# Get an instance of a logger, log some startup info
logger = logging.getLogger(__name__)


def get_import_file(filename):
    return path.join(IMPORTDIR, '%s') % filename


def import_filesummary(import_filestats):
    result = [0, 0, 0, []]
    for import_filename, status, count, filenames in import_filestats:
        if 'pending' in status:
            result[0] = count - 1
        if 'submitted' in status:
            result[0] = count - 1
            inputfiles = filenames
        if 'ingested' in status:
            result[1] = count
            try:
                result[2] = result[0] - result[1]
                result[3] = [image for image in inputfiles if image not in filenames and image != 'name']
            except:
                pass
    return result


def get_import_filelist():
    filelist = [f for f in listdir(IMPORTDIR) if isfile(join(IMPORTDIR, f))]
    import_filedict = {}
    errors = []
    for f in sorted(filelist):
        linecount, importtypes = check_file(join(IMPORTDIR, f))
        counts = [0, 0, 0, 0]
        subtotal = 0
        for i, recordtype in enumerate('M R C'.split(' ')):
            for t in importtypes:
                if '"%s"' % recordtype in t:
                    counts[i] += 1
                    subtotal += 1
        counts[3] = subtotal
        import_filedict[f] = counts
    import_filelist = [[import_filekey, False, import_filedict[import_filekey]] for import_filekey in
                       sorted(import_filedict.keys(), reverse=True)]
    return import_filelist[0:500], errors, len(import_filelist), len(errors)


def check_file(file_handle):
    file_handle.seek(0)
    lines = file_handle.read().splitlines()
    recordtypes = [f.split("\t") for f in lines]
    return len(lines), recordtypes


# following function borrowed from Django docs, w modifications
def handle_uploaded_file(f):
    destination = open(path.join(IMPORTDIR, '%s') % f.name, 'wb+')
    with destination:
        for chunk in f.chunks():
            destination.write(chunk)
    destination.close()
    return check_file(f)


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
        return 0, '', value
    if mapping_key[2] == 'literal':
        return 0, 'a literal', value
    elif mapping_key[2] == 'date':
        return 0, 'a date', value
    elif mapping_key[2] == 'key':
        return 0, 'key', value
    elif mapping_key[2] == 'refname':
        refname = get_auth_item(value, mapping_key[5])
        if refname[0] != 'OK':
            return 1, "refname for '%s' not found" % value, refname
        else:
            return 0, 'a refname', refname
    elif mapping_key[2] == 'static':
        return 1, 'static vocab terms not validated yet', 'NotValidated X X X X'.split(' ')
    elif mapping_key[2] == 'integer':
        try:
            int(value)
            return 0, 'an integer', int(value)
        except:
            return 1, '"%s" is not an integer. ' % value
    elif mapping_key[2] == 'float':
        try:
            float(value)
            return 0, 'a float', float(value)
        except:
            return 1, '"%s" is not a float. ' % value
    else:
        return 0, 'unvalidated', value


def validate_cell(CSPACE_MAPPING, key, values):
    num_problems = 0
    messages = []
    validated_values = {}
    if key in CSPACE_MAPPING:
        for v in values:
            isaproblem, m, validated_value = check_cell_in_cspace(CSPACE_MAPPING[key], key, v)
            validated_values[v] = validated_value
            num_problems += isaproblem
            if isaproblem != 0:
                if num_problems == 10:
                    messages.append('[...]')
                elif num_problems > 10:
                    continue
                else:
                    messages.append(m)
    else:
        messages = ['column ignored: not a mapped field']
    valid_label = 'OK' if num_problems == 0 else 'Not OK'
    return valid_label, num_problems, '; '.join(messages), validated_values


def map2cspace(CSPACE_MAPPING, cell, j, stats, header):
    #column = header[j]
    stat = stats[0][j]
    value_dict = stat[7]
    if cell in value_dict:
        if type(value_dict[cell]) == type([]):
            if value_dict[cell][0] == 'OK':
                return value_dict[cell][3]
            else:
                return ''
        else:
            return value_dict[cell]
    else:
        return cell


def validate_columns(CSPACE_MAPPING, matrix, header):
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
        valid_label, num_problems, message, validated_values = validate_cell(CSPACE_MAPPING, key, types[key])
        stats.append((key, len(types[key]), sum(types[key].values()), valid_label, num_problems, message, types[key], validated_values))

    # filter out columns that have no data.
    #stats = [s for s in stats if s[1] > 0]
    return stats, 'column types tokens status problems message types valid_values'.split(' ')


def check_columns(labels, header, field_map):
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


def getQueue(import_filetypes):
    return [x for x in listdir(IMPORTDIR) if '.csv' in x]


def getCSID(objectnumber):
    # dummy function, for now
    objectCSID = objectnumber
    return objectCSID

def extract_tag(xml, tag):
    element = xml.find('.//%s' % tag)
    return element.text


def extract_refname(xml):

    try:
        cspaceXML = fromstring(xml)
        totalItems = int(cspaceXML.find('.//totalItems').text)
        if totalItems == 0:
            return 'NotFound X X X X'.split(' ')
        items = cspaceXML.findall('.//list-item')
        for i in items:
            csid = i.find('.//csid')
            csid = csid.text
            try:
                try:
                    termDisplayName = extract_tag(i, 'termDisplayName')
                except:
                    try:
                        termDisplayName = extract_tag(i, 'displayName')
                    except:
                        pass
                refName = extract_tag(i, 'refName')
                updated_at = extract_tag(i, 'updatedAt')
            except:
                print 'could not get termDisplayName or refName or updatedAt from %s' % csid
                return 'Failed X X X X'.split(' ')
            return ['OK', csid, termDisplayName, refName, updated_at]
    except:
        return 'Failed X X X X'.split(' ')


def get_auth_item(term, authority):
    url = '%s/cspace-services/%s/items?kw=%s&wf_deleted=false&pgSz=%s' % (http_parms.server, authority, urllib.quote_plus(term), 2)
    # response = requests.get(url, params={'q': taxon_prefix})
    response = requests.get(url, auth=HTTPBasicAuth(http_parms.username, http_parms.password))
    if response.status_code != 200:
        #print "search failed!"
        #print "response: %s" % response.status_code
        #print response.content
        error_msg = "HTTP%s X X X X" % response.status_code
        return error_msg.split(' ')
    response.raise_for_status()

    response.encoding = 'utf-8'
    refname_result = extract_refname(response.content)
    return refname_result
    #return extract_refname(response)


def getVocab(vocabcsid, request):
    '''
    
    https://pahma-dev.cspace.berkeley.edu/cspace-services/vocabularies
    
    <ns2:abstract-common-list xmlns:ns2="http://collectionspace.org/services/jaxb">
    <pageNum>0</pageNum>
    <pageSize>40</pageSize>
    <itemsInPage>40</itemsInPage>
    <totalItems>62</totalItems>
    <fieldsReturned>
    csid|uri|refName|updatedAt|workflowState|shortIdentifier|displayName|vocabType
    </fieldsReturned>
    <list-item>
    <csid>92a0f614-de7e-4959-8870</csid>
    <uri>/vocabularies/92a0f614-de7e-4959-8870</uri>
    <refName>
    urn:cspace:pahma.cspace.berkeley.edu:vocabularies:name(assocpeople)'assocpeople'
    </refName>
    <updatedAt>2017-06-21T20:38:07Z</updatedAt>
    <workflowState>project</workflowState>
    <shortIdentifier>assocpeople</shortIdentifier>
    <displayName>assocpeople</displayName>
    </list-item>
    
    https://pahma-dev.cspace.berkeley.edu/cspace-services/vocabularies/92a0f614-de7e-4959-8870/items
    
    <ns2:abstract-common-list xmlns:ns2="http://collectionspace.org/services/jaxb">
    <pageNum>0</pageNum>
    <pageSize>40</pageSize>
    <itemsInPage>10</itemsInPage>
    <totalItems>10</totalItems>
    <fieldsReturned>
    csid|uri|refName|updatedAt|workflowState|order|termStatus|displayName|shortIdentifier
    </fieldsReturned>
    <list-item>
    <csid>604f27b0-d9a6-4c1c-8380</csid>
    <uri>
    /vocabularies/92a0f614-de7e-4959-8870/items/604f27b0-d9a6-4c1c-8380
    </uri>
    <refName>
    urn:cspace:pahma.cspace.berkeley.edu:vocabularies:name(assocpeople):item:name(assocpeopletype00)'gathered/collected by'
    </refName>
    <updatedAt>2017-06-21T20:38:07Z</updatedAt>
    <workflowState>project</workflowState>
    <termStatus>active</termStatus>
    <displayName>gathered/collected by</displayName>
    <shortIdentifier>assocpeopletype00</shortIdentifier>
    </list-item>
    
    :param vocabcsid: 
    :param request: 
    :return: 
    ''''''
        connection = cspace.connection.create_connection(config, request.user)
        (url, data, statusCode,elapsedtime) = connection.make_get_request(
            'cspace-services/%s?kw=%s&wf_deleted=false' % ('collectionobjects', vocabcsid))
        # ...collectionobjects?kw=%27orchid%27&wf_deleted=false
        cspaceXML = fromstring(data)
        items = cspaceXML.findall('.//list-item')
        results = []
        for i in items:
            outputrow = []
            csid = i.find('.//csid')
            csid = csid.text
            objectNumber = i.find('.//objectNumber')
            objectNumber = objectNumber.text
            hostname = connection.protocol + ':' + connection.hostname
            if connection.port != '': hostname = hostname + ':' + connection.port
            link = '%s/collectionspace/ui/%s/html/cataloging.html?csid=%s' % (hostname, connection.tenant, csid)
            outputrow.append(link)
            outputrow.append(objectNumber)
            additionalfields = []
            for field in ['objectName', 'title', 'updatedAt']:
                element = i.find('.//%s' % field)
                element = '' if element is None else element.text
                # extract display name if a refname... nb: this pattern might do damage in some cases!
                element = re.sub(r"^.*\)'(.*)'$", "\\1", element)
                additionalfields.append(element)
            outputrow.append(additionalfields)
            results.append(outputrow)
            '''
