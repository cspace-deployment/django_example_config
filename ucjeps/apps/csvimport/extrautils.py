import csv
import codecs
import re
import json
import logging
import datetime, time

from os import path, listdir, stat
from os.path import isfile, isdir, join
from xml.sax.saxutils import escape

from common import cspace  # we use the config file reading function
from common.utils import deURN
from cspace_django_site import settings

config = cspace.getConfig(path.join(settings.BASE_PARENT_DIR, 'config'), 'csvimport')
QUEUEDIR = config.get('files', 'directory')
CODEPATH = path.join(settings.BASE_PARENT_DIR, 'csvimport')
SERVERLABEL = config.get('info', 'serverlabel')
SERVERLABELCOLOR = config.get('info', 'serverlabelcolor')
INSTITUTION = config.get('info', 'institution')
FIELDS2WRITE = 'job filename handling status'.split(' ')
BATCHPARAMETERS = 'None'

if isdir(QUEUEDIR):
    print "Using %s as working directory for csvimport files" % QUEUEDIR
else:
    print "%s is not an existing directory, using /tmp instead for csvimport files" % QUEUEDIR
    QUEUEDIR = '/tmp'
    # raise Exception("csvImport working directory %s does not exist. this webapp will not work without it!" % QUEUEDIR)

JOBDIR = path.join(QUEUEDIR, '%s')

# Get an instance of a logger, log some startup info
logger = logging.getLogger(__name__)


def getJobfile(jobnumber):
    return JOBDIR % jobnumber

priority =   'input counted validated added updated undo'.split(' ')
next_steps = 'count validate update undo undo'.split(' ')

def jobsummary(jobstats):
    results = [0, 0, 0, '', 'completed']
    first_date = ''
    new_order = 0
    update_type = ''
    for jobfile, status, count, lines, date_uploaded in jobstats:
        if date_uploaded > first_date:
            first_date = date_uploaded
        if status in ['add', 'update']:
            update_type = status
        elif status == 'inprogress':
            update_type = 'in progress'
        if '.csv' in jobfile:
            continue
        if status in priority:
            order = priority.index(status)
            if order > new_order:
                new_order = order
    try:
        next = next_steps[new_order]
    except:
        next = 'unknown'

    if update_type == 'in progress' or next == 'update':
        next = update_type

    results[3] = first_date
    results[0] = count - 1
    results[4] = next
    if results[2] > 0 and results[4] == 'completed':
        results[4] = 'problem'
    return results


def getJoblist(request):

    if 'num2display' in request.POST:
        num2display = int(request.POST['num2display'])
    else:
        num2display = 50

    jobpath = JOBDIR % ''
    #filelist = [f for f in listdir(jobpath) if isfile(join(jobpath, f)) and ('.csv' in f or 'trace.log' in f)]
    filelist = [f for f in listdir(jobpath) if isfile(join(jobpath, f))]
    jobdict = {}
    errors = []
    filelist = sorted(filelist, reverse=True)
    for f in sorted(filelist, reverse=True):
        if len(jobdict.keys()) > num2display:
            pass
            records = []
        else:
            # we only need to count lines if the file is within range...
            linecount, records, date_uploaded = checkFile(join(jobpath, f))
        parts = f.split('.')
        try:
            file_type = parts[1]
        except:
            file_type = 'unknown'
        jobkey = parts[0]
        if not jobkey in jobdict: jobdict[jobkey] = []
        jobdict[jobkey].append([f, file_type, linecount, records, date_uploaded])
    joblist = [[jobkey, jobdict[jobkey], jobsummary(jobdict[jobkey])] for jobkey in sorted(jobdict.keys(), reverse=True) if jobkey != '']
    num_jobs = len(joblist)
    return joblist[0:num2display], errors, num_jobs, len(errors)


def checkFile(filename):
    file_handle = open(filename)
    date_uploaded  = datetime.datetime.fromtimestamp(path.getmtime(filename)).strftime("%Y-%m-%d %H:%M:%S")
    lines = [l for l in file_handle.read().splitlines()]
    #specimens = [f.split("\t")[0] for f in lines]
    #specimens = [f.split("|")[0] for f in specimens]
    return len(lines), [], date_uploaded


def writeCsv(filename, items, writeheader):
    filehandle = codecs.open(filename, 'w', 'utf-8')
    writer = csv.writer(filehandle, delimiter='|')
    writer.writerow(writeheader)
    for item in items:
        row = []
        for x in writeheader:
            if x in item.keys():
                cell = str(item[x])
                cell = cell.strip()
                cell = cell.replace('"', '')
                cell = cell.replace('\n', '')
                cell = cell.replace('\r', '')
            else:
                cell = ''
            row.append(cell)
        writer.writerow(row)
    filehandle.close()


# this somewhat desperate function makes an html table from a tab- and newline- delimited string
def reformat(filecontent):
    result = deURN(filecontent)
    result = result.replace('\n','<tr><td>')
    result = result.replace('\t','<td>')
    result = result.replace('|','<td>')
    result = result.replace('False','<span class="error">False</span>')
    result += '</table>'
    return '<table width="100%"><tr><td>\n' + result