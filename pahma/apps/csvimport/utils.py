import csv
import codecs
import re
import json
import logging
from xml.sax.saxutils import escape
import hashlib

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

def load_mapping_file(mapping_file):
    mapping_file = path.join(path.join(settings.BASE_PARENT_DIR, 'config'), 'DWC2CSPACE.csv')
    delim = '\t'
    cspace_mapping = {}
    with open(mapping_file, 'r') as f1:
        reader = UnicodeReader(f1, delimiter=delim, quoting=csv.QUOTE_NONE, quotechar=chr(255))
        for lineno, row in enumerate(reader):
            # FIMS field name	Cspace collectionobject tag	context tag	data type	check exists?
            row_id, input_field, cspace_field, context_tag, data_type, check_exists = row
            if input_field != '' and input_field[0] == '#':
                continue
            cspace_mapping[input_field] = (cspace_field, context_tag, data_type, check_exists)
    return cspace_mapping

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


def check_cell_in_cspace(CSPACE_MAPPING, key, value):
    if value == '':
        return 0, ''
    if CSPACE_MAPPING[key][2] == 'literal':
        return 0, 'a literal'
    elif CSPACE_MAPPING[key][2] == 'refname':
        return 1, 'refnames not validated yet'
    elif CSPACE_MAPPING[key][2] == 'vocab':
        return 1, 'vocabulary terms not validated yet'
    elif CSPACE_MAPPING[key][2] == 'integer':
        try:
            int(value)
        except:
            return 1, '%s is not an integer' % value
    else:
        return 0, 'unvalidated'


def validate_cell(CSPACE_MAPPING, key, values):
    import random
    num_problems = 0
    message = ''
    for v in values:
        if key in CSPACE_MAPPING:
            i, m = check_cell_in_cspace(CSPACE_MAPPING, key, v)
            num_problems += i
            if m not in message:
                if num_problems == 10:
                    message += '[...]'
                elif num_problems > 10:
                    continue
                else:
                    message += '%s  ' % m
        else:
            message = 'column ignored: not a mappable field'
    valid_label = 'OK' if num_problems == 0 else 'Not OK'
    return valid_label, num_problems, message


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
        valid_label, num_problems, message = validate_cell(CSPACE_MAPPING, key, types[key])
        stats.append((key, len(types[key]), sum(types[key].values()), valid_label, num_problems, message))

    # filter out columns that have no data.
    stats = [s for s in stats if s[1] > 0]
    return stats, 'column types tokens status problems message'.split(' ')


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

