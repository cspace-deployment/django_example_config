__author__ = 'jblowe'

# import json
import traceback
import sys
# from common.cspace import logged_in_or_basicauth
from django.shortcuts import render, HttpResponse, render_to_response
from django.template import RequestContext
import time, datetime, re
from utils import SERVERINFO, TITLE, handle_uploaded_file, getCSID, get_import_file, loginfo, RECORDTYPES
from utils import check_columns, count_columns, validate_columns

# read common config file, just for the version info
from common.appconfig import loadConfiguration

prmz = loadConfiguration('common')


def prepareFiles(request, mergeinput):
    import_files = []
    numProblems = 0
    matrix = None

    for lineno, afile in enumerate(request.FILES.getlist('importfile')):
        fileinfo = {'id': lineno, 'name': afile.name, 'status': '',
                    'date': time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime())}
        # always use the current date as the date for the filename checking
        today = time.strftime("%Y-%m-%d", time.localtime())
        try:
            print "%s %s: %s %s (%s %s)" % ('id', lineno, 'name', afile.name, 'size', afile.size)
            count, matrix = handle_uploaded_file(afile)
            fileinfo['status'] = 'OK'
        except:
            fileinfo['status'] = "error! %s" % traceback.format_exc()
            sys.stderr.write("error! %s" % traceback.format_exc())
            numProblems += 1

        import_files.append(fileinfo)

    errormsg = ''
    if numProblems > 0:
        errormsg = 'Errors found, abandoning upload. Please fix and try again.'
    elif len(import_files) == 0:
        errormsg = 'Please select a file to upload.'
    else:
        import_filenumber = time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime())

        if 'doimport' in request.POST:
            if not mergeinput:
                loginfo('start', get_import_file('input', import_filenumber), request)
                try:
                    pass
                except:
                    loginfo('error', "Execution failed.", request)
                loginfo('finish', get_import_file('input', import_filenumber), request)

    if import_files == []:
        import_files = [{'name': ''}]

    return import_files, numProblems, errormsg, matrix

def get_fields(request):
    m = []
    for x in request:
        if 'col.' in x:
            m.append(request.getlist(x))
    m = [[m[j][i] for j in range(len(m))] for i in range(len(m[0]))]
    return m

def get_action(action):

    if action == 'add':
        cspaceaction = 'Add Records'
    elif action == 'update':
        cspaceaction = 'Update existing Records'
    elif action == 'both':
        cspaceaction = 'Update existing Records, Add new records'
    elif action == 'validate':
        cspaceaction = 'Revalidate this file again (I have made changes in CSpace).'
    elif action == 'count':
        cspaceaction = 'Count values in input file.'
    else:
        cspaceaction = None

    return cspaceaction

# @login_required()
def upload_file(request):
    elapsedtime = time.time()
    status = 'up'
    errors = []
    message = ''
    update_type = True
    import_files = [{'name': ''}]
    constants = {}
    numProblems = 0
    matrix = None
    labels = None
    keyrow = None
    columnhandling = None
    recordtype = None
    use_header = None
    action = None
    checkboxes = {
        'recordtype':'Record Type',
        'action':'Action',
        'update_type':'Merge or Replace',
        'use_header':'Header option'
    }

    if request.POST:

        for form_value in checkboxes:
            if not form_value in request.POST:
                errors.append("Please check an option for %s." % checkboxes[form_value])

        if not 'update_type' in request.POST:
            update_type = False

        if len(errors) == 0:

            import_files, numProblems, errormsg, matrix = prepareFiles(request, update_type)
            if errormsg != '':
                errors.append(errormsg)

        if len(errors) == 0:

            use_header = request.POST['use_header']
            action = request.POST['action']
            recordtype = request.POST['recordtype']
            update_type = request.POST['update_type']
            if 'use' in use_header or 'ignore' in use_header:
                labels = matrix[0]
                matrix = matrix[1:]
            elif 'none' in use_header:
                labels = ['column %s' % (i + 1) for i, v in enumerate(matrix[0])]
            if action == 'count':
                message = '%s rows examined.' % len(matrix)
                matrix, labels = count_columns(matrix, labels)
            elif action == 'validate':
                message = '%s rows validated.' % len(matrix)
                CSPACE_MAPPING = RECORDTYPES[recordtype][2]
                matrix, labels = validate_columns(CSPACE_MAPPING, matrix, labels)
            columnhandling = check_columns(labels, request.POST['use_header'], request.POST['recordtype'])
            try:
                keyrow = labels.index('id')
            except:
                keyrow = -1
            recordtype = request.POST['recordtype']

    cspaceaction = get_action(action)
    timestamp = time.strftime("%b %d %Y %H:%M:%S", time.localtime())
    rtypes = [[RECORDTYPES[r][0], r] for r in RECORDTYPES.keys()]
    elapsedtime = time.time() - elapsedtime

    return render_to_response('uploadimport.html',
                  {'apptitle': TITLE, 'serverinfo': SERVERINFO, 'import_upload_files': import_files,
                   'count': len(import_files), 'version': prmz.VERSION, 'matrix': matrix, 'labels': labels,
                   'keyrow': keyrow, 'columnhandling': columnhandling, 'recordtypes': rtypes,
                   'cspaceaction': cspaceaction, 'message': message, 'errors': errors,
                   'constants': constants, 'filename': import_files[0]['name'],
                   'use_header': use_header, 'recordtype': recordtype, 'action': action, 'update_type': update_type,
                   'status': status, 'timestamp': timestamp, 'directory': 'input', 'numProblems': numProblems,
                   'elapsedtime': '%8.2f' % elapsedtime}, context_instance=RequestContext(request))


# @login_required()
def process_file(request):

    elapsedtime = time.time()
    status = 'up'
    errors = []
    message = ''
    constants = {}
    update_type = True

    # filename = request.GET['filename']
    # directory = request.GET['directory']
    # f = open(get_import_file(directory, filename), "rb")
    timestamp = time.strftime("%b %d %Y %H:%M:%S", time.localtime())
    #cspaceaction = 'x'
    #columnhandling = checkcolumns(labels, request.POST['header'], request.POST['recordtype'])
    elapsedtime = time.time() - elapsedtime
    matrix = get_fields(request.POST)
    labels = request.POST['labels']
    action = request.POST['action']
    cspaceaction = get_action(action)

    use_header = request.POST['header']
    recordtype = request.POST['recordtype']
    action = request.POST['action']
    numProblems = 0

    return render_to_response('uploadimport.html',
                  {'apptitle': TITLE, 'serverinfo': SERVERINFO,
                   'version': prmz.VERSION, 'matrix': matrix, 'labels': labels,
                   'cspaceaction': cspaceaction, 'message': message, 'errors': errors,
                   'header': use_header, 'recordtype': recordtype, 'action': action, 'update_type': update_type,
                   'status': status, 'timestamp': timestamp, 'directory': 'input', 'numProblems': numProblems,
                   'elapsedtime': '%8.2f' % elapsedtime}, context_instance=RequestContext(request))


# @login_required()
def importdata(request):
    filename = request.GET['filename']
    directory = request.GET['directory']
    f = open(get_import_file(directory, filename), "rb")
    status = 'up'
    timestamp = time.strftime("%b %d %Y %H:%M:%S", time.localtime())
    return render(request, 'uploadimport.html',
                  {'timestamp': timestamp, 'version': prmz.VERSION,
                   'status': status, 'apptitle': TITLE, 'serverinfo': SERVERINFO,
                   'filecontent': f.read(), 'filename': filename, 'directory': directory})
