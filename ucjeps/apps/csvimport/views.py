__author__ = 'jblowe'

from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
import json
import sys
import traceback
#from common.cspace import logged_in_or_basicauth
from django.shortcuts import render, HttpResponse, redirect
from wsgiref.util import FileWrapper
from os import path, remove
import glob
import logging
import time, datetime
from copy import deepcopy

from utils import SERVERINFO, TITLE, loginfo
from utils import check_columns, get_recordtypes, handle_uploaded_file


from extrautils import SERVERLABEL, SERVERLABELCOLOR, CODEPATH, INSTITUTION, JOBDIR
from extrautils import getJobfile, getJoblist

RECORDTYPES = get_recordtypes()

try:
    from xml.etree.ElementTree import tostring, parse, Element, fromstring
except:
    print("could not import with xml.etree.ElementTree")
    raise

# read common config file, just for the version info
from common.appconfig import loadConfiguration
prmz = loadConfiguration('common')

import subprocess
#from .models import AdditionalInfo

#additionalInfo = AdditionalInfo.objects.filter(live=True)

CHECKBOXES = {
    'recordtype': 'Record Type',
    'action': 'Action',
    'update_type': 'Merge or Replace',
    'use_header': 'Header option'
}

# STATUSES = 'input count valid invalid terms add update'.split(' ')
STATUSES = 'input count invalid add update terms add-audit'.split(' ')
LOGS = 'counted validated added updated'.split(' ')

# Get an instance of a logger, log some startup info
logger = logging.getLogger(__name__)
logger.info('%s :: %s :: %s' % ('csvimport startup', '-', '-'))


def setContext(context, elapsedtime):
    # context['status'] = 'up'
    #context['additionalInfo'] = additionalInfo
    context['imageserver'] = prmz.IMAGESERVER
    context['cspaceserver'] = prmz.CSPACESERVER
    context['institution'] = prmz.INSTITUTION
    # context['csrecordtype'] = prmz.CSRECORDTYPE
    context['csrecordtype'] = 'media'
    context['apptitle'] = TITLE
    context['version'] = prmz.VERSION
    context['elapsedtime'] = '%8.2f' % elapsedtime
    context['serverlabel'] = SERVERLABEL
    context['serverlabelcolor'] = SERVERLABELCOLOR
    context['timestamp'] = time.strftime("%b %d %Y %H:%M:%S", time.localtime())
    return context


def prepareFiles(request, context):

    jobinfo = {}
    specimens = []
    for lineno, afile in enumerate(request.FILES.getlist('importfile')):
        # print afile
        try:
            print "%s %s: %s %s (%s %s)" % ('id', lineno + 1, 'name', afile.name, 'size', afile.size)
            
            handle_uploaded_file(afile)

        except:
            sys.stderr.write("error! file=%s %s" % (afile.name, traceback.format_exc()))
            specimens.append({'name': afile.name, 'size': afile.size, 'error': 'problem uploading file or extracting image metadata, not processed'})

    return jobinfo, specimens


def setConstants(request):

    context = {}

    context['statuses'] = STATUSES
    context['logs'] = LOGS
    context['recordtypes'] = [[RECORDTYPES[r][0], r] for r in RECORDTYPES.keys()]

    return context


@login_required()
def upload_file(request):
    elapsedtime = time.time()
    context = setConstants(request)
    context['jobnumber'] = time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime())

    if request.POST:
        jobinfo, rows = prepareFiles(request, context)
    else:
        jobinfo = {}
        rows = []

    elapsedtime = time.time() - elapsedtime
    logger.info('%s :: %s :: %s' % ('csvimport job ', context['jobnumber'], '-'))
    context = setContext(context, elapsedtime)

    context['jobinfo'] = jobinfo
    #context['rows'] = rows
    context['count'] = len(rows)
    context['fileview'] = 'none'

    return showqueue(request)


@login_required()
def downloadresults(request, filename):
    f = open(getJobfile(filename), "rb")
    response = HttpResponse(FileWrapper(f), content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="%s"' % filename
    return response


@login_required()
def showresults(request, filename):
    elapsedtime = 0.0
    context = setConstants(request)
    f = open(getJobfile(filename), "rb")
    filecontent = f.read()
    f.close()
    context['filename'] = filename
    context['logcontent'] = filecontent
    #context['filecontent'] = reformat(filecontent)
    elapsedtime = time.time() - elapsedtime
    context = setContext(context, elapsedtime)
    context['fileview'] = 'inline'

    return render(request, 'csvimport.html', context)
                              

@login_required()
def deletejob(request, jobname):
    try:
        filelist = glob.glob(JOBDIR % jobname + ".*")
        for filename in filelist:
            remove(filename)
            logger.info('%s :: %s' % ('csvimport file deleted', filename))

    except:
        logger.info('%s :: %s' % ('csvimport tried but failed to delete job', jobname))
    return showqueue(request)


@login_required()
def showqueue(request):
    elapsedtime = time.time()
    context = setConstants(request)
    jobs, errors, jobcount, errorcount = getJoblist(request)
    display_type = 'checkjobs'
    if 'checkjobs' in request.POST:
        display_type = 'checkjobs'
    elif 'showerrors' in request.POST:
        display_type = 'showerrors'
    context['display'] = display_type
    context['jobs'] = jobs
    context['errors'] = errors
    context['jobcount'] = jobcount
    context['errorcount'] = errorcount
    elapsedtime = time.time() - elapsedtime
    context = setContext(context, elapsedtime)
    context['fileview'] = 'none'

    labels, matrix, message, rtypes = show_csv_config(request)

    context['labels'] = labels
    context['matrix'] = matrix
    context['message'] = message
    context['rtypes'] = rtypes

    return render(request, 'csvimport.html', context)


@login_required()
def nextstep(request, step, filename):
    elapsedtime = time.time()
    context = setConstants(request)
    context['display'] = 'checkjobs'
    context = setContext(context, elapsedtime)
    messages = []

    messages.append('estimated time = %8.1f seconds' % (len([]) * 10 / 60.0))

    loginfo('start', getJobfile(filename), request)
    try:
        file_is_OK = True
        if file_is_OK:
            script = path.join(CODEPATH, '%s.sh' % step)
            p_object = subprocess.Popen([script, JOBDIR % filename, 'collectionobjects'])
            if p_object._child_created:
                pid = p_object.pid
                loginfo('process', filename + ": Child returned %s" % p_object.returncode, request)
                messages.append('process ' + filename + ": Child returned %s" % p_object.returncode)
            else:
                loginfo('process', filename + " Child had returncode %s" % p_object.returncode, request)
    except OSError as e:
        messages.append('job failed')
        loginfo('error', "Execution failed: %s" % e, request)
    loginfo('finish', getJobfile(filename), request)

    context['messages'] = messages
    context['elapsedtime'] = time.time() - elapsedtime

    time.sleep(1)

    return showqueue(request)


@login_required()
def show_csv_config(request):

    recordtype = 'collectionobjects'

    matrix = deepcopy(RECORDTYPES[recordtype][2][0])
    # convert from dict of tuples to list of tuples
    matrix = [[m, ] + matrix[m] for m in matrix]
    matrix = [[m[i] for i in (0, 1, 3, 6, 5)] for m in matrix]
    matrix = sorted(matrix, key=lambda x: x[4])
    #labels = 'input_column,cspace_field,context_tag,data_type,check_exists,row_id,authority or vocabulary'.split(',')
    labels = 'input column,cspace field,data type,authority or vocabulary,row id'.split(',')
    columnhandling = check_columns(labels, 'none', recordtype)
    #message = "%s 'actionable' fields configured in config file." % len(matrix)
    message = "'Mappable' fields for %s" % recordtype
    rtypes = [[RECORDTYPES[r][0], r] for r in RECORDTYPES.keys()]

    return labels, matrix, message, rtypes