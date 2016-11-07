__author__ = 'jblowe'

from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
import json
# from common.cspace import logged_in_or_basicauth
from django.shortcuts import render, HttpResponse
import time, datetime, re
from utils import SERVERINFO, TITLE, POSTBLOBPATH, handle_uploaded_file, getCSID, get_tricoder_file, get_tricoder_filelist, loginfo

# read common config file, just for the version info
from common.appconfig import loadConfiguration
prmz = loadConfiguration('common')

import subprocess
from .models import AdditionalInfo

class trcdr:  # empty class for tricoder metadata
    pass


def prepareFiles(request, validateonly):
    tricoder_fileinfo = {}
    tricoder_files = []
    numProblems = 0
    for lineno, afile in enumerate(request.FILES.getlist('tricoderfiles')):
        # print afile
        # we gotta do this for now!
        if 'barcode.' not in afile.name: afile.name = 'barcode.' + afile.name
        fileinfo = {'id': lineno, 'name': afile.name, 'status': '', 'date': time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime())}
        # always use the current date as the date for the filename checking
        today = time.strftime("%Y-%m-%d", time.localtime())
        filenamepattern = r'^barcode.TRIDATA_' + re.escape(today) + r'_[\w_\.]+\.DAT$'
        if not re.match(filenamepattern, afile.name):
            fileinfo['status'] = 'filename is not valid'
            numProblems += 1
        else:
            try:
                print "%s %s: %s %s (%s %s)" % ('id', lineno, 'name', afile.name, 'size', afile.size)
                if not validateonly:
                    handle_uploaded_file(afile)
                fileinfo['status'] = 'OK'
            except:
                if validateonly:
                    fileinfo['status'] = 'validation failed'
                else:
                    fileinfo['status'] = 'file handling problem, not uploaded'
                numProblems += 1

        tricoder_files.append(fileinfo)

    if numProblems > 0:
        errormsg = 'Errors found, abandoning upload. Please fix and try again.'
    else:
        tricoder_filenumber = time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime())
        tricoder_fileinfo['tricoder_filenumber'] = tricoder_filenumber
        tricoder_fileinfo['estimatedtime'] = '%8.1f' % (len(tricoder_files) * 10 / 60.0)

        if 'createtricoder' in request.POST:
            tricoder_fileinfo['status'] = 'createtricoder'
            if not validateonly:
                loginfo('start', get_tricoder_file('input',tricoder_filenumber), request)
                try:
                    retcode = subprocess.call(
                        [POSTBLOBPATH, get_tricoder_file('input',tricoder_filenumber)])
                    if retcode < 0:
                        loginfo('process', tricoder_filenumber + " Child was terminated by signal %s" % -retcode,
                                request)
                    else:
                        loginfo('process', tricoder_filenumber + ": Child returned %s" % retcode, request)
                except OSError as e:
                    loginfo('error', "Execution failed: %s" % e, request)
                loginfo('finish', get_tricoder_file('input',tricoder_filenumber), request)

        elif 'uploadtricoder' in request.POST:
            tricoder_fileinfo['status'] = 'uploadtricoder'
        else:
            tricoder_fileinfo['status'] = 'No status possible'

    return tricoder_fileinfo, tricoder_files, numProblems


def setConstants(request, trcdr):
    trcdr.validateonly = 'validateonly' in request.POST
    constants = {}
    return constants


@csrf_exempt
#@logged_in_or_basicauth()
def rest(request, action):
    elapsedtime = time.time()
    status = 'error'  # assume murphy's law applies...

    if request.FILES:
        setConstants(request, trcdr)
        tricoder_fileinfo, tricoder_files = prepareFiles(request, trcdr.validateonly)
        status = 'ok'  # OK, I guess it doesn't after all
    else:
        tricoder_fileinfo = {}
        tricoder_files = []
        status = 'no post seen'  # OK, I guess it doesn't after all
        return HttpResponse(json.dumps({'status': status}))

    timestamp = time.strftime("%b %d %Y %H:%M:%S", time.localtime())
    elapsedtime = time.time() - elapsedtime

    return HttpResponse(json.dumps(
        {'status': status, 'tricoder_files': tricoder_files, 'tricoder_fileinfo': tricoder_fileinfo,
         'elapsedtime': '%8.2f' % elapsedtime}), content_type='text/json')


@login_required()
def uploadfiles(request):
    elapsedtime = time.time()
    status = 'up'
    constants = setConstants(request, trcdr)

    if request.POST:
        constants = setConstants(request, trcdr)
        tricoder_fileinfo, tricoder_files, numProblems = prepareFiles(request, trcdr.validateonly)
    else:
        tricoder_fileinfo = {}
        tricoder_files = []
        constants = {}
        numProblems = 0

    timestamp = time.strftime("%b %d %Y %H:%M:%S", time.localtime())
    elapsedtime = time.time() - elapsedtime

    return render(request, 'uploadtricoder.html',
                  {'apptitle': TITLE, 'serverinfo': SERVERINFO, 'tricoder_upload_files': tricoder_files,
                   'count': len(tricoder_files), 'version': prmz.VERSION,
                   'constants': constants, 'tricoder_fileinfo': tricoder_fileinfo, 'validateonly': trcdr.validateonly,
                   'status': status, 'timestamp': timestamp, 'directory': 'input', 'numProblems': numProblems,
                   'elapsedtime': '%8.2f' % elapsedtime})


@login_required()
def checkfilename(request):
    elapsedtime = time.time()
    if 'filenames2check' in request.POST and request.POST['filenames2check'] != '':
        listoffilenames = request.POST['filenames2check']
        filenames = listoffilenames.split(' ')
        objectnumbers = [o for o in filenames]
    else:
        objectnumbers = []
        listoffilenames = ''
    elapsedtime = time.time() - elapsedtime
    status = 'up'
    timestamp = time.strftime("%b %d %Y %H:%M:%S", time.localtime())

    return render(request, 'uploadtricoder.html', {'filenames2check': listoffilenames, 'version': prmz.VERSION,
                                                   'objectnumbers': objectnumbers, 'timestamp': timestamp,
                                                   'elapsedtime': '%8.2f' % elapsedtime, 'directory': 'input',
                                                   'status': status, 'apptitle': TITLE, 'serverinfo': SERVERINFO})


@login_required()
def showresults(request):
    filename = request.GET['filename']
    directory = request.GET['directory']
    f = open(get_tricoder_file(directory,filename), "rb")
    status = 'up'
    timestamp = time.strftime("%b %d %Y %H:%M:%S", time.localtime())
    return render(request, 'uploadtricoder.html',
                  {'timestamp': timestamp, 'version': prmz.VERSION,
                   'status': status, 'apptitle': TITLE, 'serverinfo': SERVERINFO,
                   'filecontent': f.read(), 'filename': filename, 'directory': directory})


@login_required()
def showqueue(request):
    elapsedtime = time.time()
    directory = None
    tricoder_files, errors, tricoder_filecount, errorcount = get_tricoder_filelist('')
    if 'checkpending' in request.POST:
        directory = 'input'
    elif 'checkprocessed' in request.POST:
        directory = 'processed'
    elif 'checkfailed' in request.POST:
        directory = 'bad_barcode'
    else:
        errors = None
        count = 0
    if directory:
        tricoder_files, errors, tricoder_filecount, errorcount = get_tricoder_filelist(directory)
    else:
        tricoder_files = None

    if 'showerrors' in request.POST:
        tricoder_files = None

    elapsedtime = time.time() - elapsedtime
    status = 'up'
    timestamp = time.strftime("%b %d %Y %H:%M:%S", time.localtime())

    return render(request, 'uploadtricoder.html',
                  {'timestamp': timestamp, 'version': prmz.VERSION,
                   'elapsedtime': '%8.2f' % elapsedtime, 'directory': directory,
                   'status': status, 'apptitle': TITLE, 'serverinfo': SERVERINFO, 'tricoder_files': tricoder_files,
                   'tricoder_filecount': tricoder_filecount, 'stats': 'M R C Total'.split(' '),
                   'errors': errors, 'errorcount': errorcount})
