#!/usr/bin/env /var/www/venv/bin/python

import traceback
import cgitb; cgitb.enable()  # for troubleshooting
from cswaConstants import selectWebapp
from cswaUtils import *
from cswaObjDetails import *

reload(sys)
sys.setdefaultencoding('utf-8')

def main(request, updateType):

    # NB we convert FieldStorage to a dict, but we need the actual form for barcode upload...
    #actualform = cgi.FieldStorage()
    form       = {}
    for r in request.POST.keys():
        form[r] = request.POST[r]

    if request.user.is_authenticated():
        form['userdata'] = request.user
    else:
        return "<span style='color:red'>You must be authenticated to use these Tools! Please sign in (upper right of this page).</span>"

    try:
        action = request.POST['action']
    except:
        action = ''

    checkServer = form.get('check')

    config  = getConfig(request, updateType)
    # we don't do anything with debug now, but it is a comfort to have
    debug = form.get("debug")
    html = ''

    # bail if we don't know which webapp to be...(i.e. no config object passed in from cswaMain)
    if config == False:
        html = selectWebapp(form, request)
        return html

    #updateType  = config.get('info','updatetype')

    # if action has not been set, this is the first time through, and we need to set defaults. (only 2 right now!)
    if action == 'Login':
        form['dora'] = 'alive'

    # if location2 was not specified, default it to location1
    if str(form.get('lo.location2')) == '':
        form['lo.location2'] = form.get('lo.location1')

    # same for objects
    if str(form.get('ob.objno2')) == '':
        form['ob.objno2'] = form.get('ob.objno1')

    elapsedtime = time.time()

    writeInfo2log('start', form, config, 0.0)
    html += starthtml(form,config)

    try:
        sys.stdout.flush()

        if checkServer == 'check server':
            print serverCheck(form,config)
        else:
            if action == "Enumerate Objects":
                html += doEnumerateObjects(form,config)
            elif action == "Create Labels for Locations Only":
                html += doBarCodes(form,config)
            elif action == config.get('info','updateactionlabel'):
                if   updateType == 'packinglist':  html += doPackingList(form,config)
                elif updateType == 'movecrate':    html += doUpdateLocations(form,config)
                elif updateType == 'powermove':    html += doUpdateLocations(form,config)
                elif updateType == 'grpmove':      html += doUpdateLocations(form,config)
                elif updateType == 'barcodeprint': html += doBarCodes(form,config)
                elif updateType == 'inventory':    html += doUpdateLocations(form,config)
                elif updateType == 'moveobject':   html += doUpdateLocations(form,config)
                elif updateType == 'objinfo':      html += doUpdateKeyinfo(form,config)
                elif updateType == 'keyinfo':      html += doUpdateKeyinfo(form,config)
                elif updateType == 'grpinfo':      html += doUpdateKeyinfo(form,config)
                elif updateType == 'createobjects': html += doCreateObjects(form,config)
                elif updateType == 'bulkedit':     html += doBulkEdit(form,config)
                elif updateType == 'bedlist':      html += doBedList(form,config)
                elif updateType == 'advsearch':    html += doAdvancedSearch(form,config)
                elif updateType == 'upload':       uploadFile(form,form,config)
                elif updateType == 'governmentholdings': html += doListGovHoldings(form, config)
                elif updateType == 'intake':       html += doCommitIntake(form, config)
                #elif updateType == 'editrel':      html += doRelationsEdit(form,config)
                elif updateType == 'makegroup':    makeGroup(form,config)
                elif action == "Recent Activity":
                    viewLog(form,config)
        ##    # special case: if only one location in range, jump to enumerate
        ##    elif form.getvalue("lo.location1") != '' and str(form.getvalue("lo.location1")) == str(form.getvalue("lo.location2")) :
        ##        if updateType in ['keyinfo', 'inventory']:
        ##            doEnumerateObjects(form,config)
        ##        elif updateType == 'movecrate':
        ##            doCheckMove(form,config)
        ##        else:
        ##            doLocationSearch(form,config,'nolist')
            elif action == "Search":
                if   updateType == 'packinglist':  html += doLocationSearch(form,config,'nolist')
                elif updateType == 'movecrate':    html += doCheckMove(form,config)
                elif updateType == 'grpmove':      html += doCheckGroupMove(form,config)
                elif updateType == 'powermove':    html += doCheckPowerMove(form,config)
                elif updateType == 'barcodeprint':
                    if form.get('gr.group'):
                        html += doGroupSearch(form, config, 'list')
                    elif form.get('ob.objno1'):
                        html += doOjectRangeSearch(form, config)
                    else:
                        html += doLocationSearch(form, config, 'nolist')
                elif updateType == 'bedlist':      html += doComplexSearch(form,config,'select')
                elif updateType == 'bulkedit':     html += doBulkEditForm(form,config,'nolist')
                elif updateType == 'holdings':     html += doAuthorityScan(form,config)
                elif updateType == 'locreport':    html += doAuthorityScan(form,config)
                elif updateType == 'advsearch':    html += doComplexSearch(form,config,'select')
                elif updateType == 'inventory':    html += doLocationSearch(form,config,'list')
                elif updateType == 'keyinfo':      html += doLocationSearch(form,config,'list')
                elif updateType == 'objinfo':      html += doObjectSearch(form,config,'list')
                elif updateType == 'grpinfo':      html += doGroupSearch(form,config,'list')
                elif updateType == 'createobjects': html += doCreateObjects(form,config)
                elif updateType == 'moveobject':   html += doObjectSearch(form,config,'list')
                elif updateType == 'objdetails':   html += doObjectDetails(form,config)
                #elif updateType == 'editrel':      html += doRelationsSearch(form,config)
                elif updateType == 'makegroup':    html += doComplexSearch(form,config,'select')

            elif action == "View Hierarchy":
                html += doHierarchyView(form,config)
            elif action == "View Holdings":
                html += doListGovHoldings(form,config)
            elif action in ['<<','>>']:
                print "<h3>Sorry not implemented yet! Please try again tomorrow!</h3>"
            else:
                pass
                #print "<h3>Unimplemented action %s!</h3>" % str(action)

    except:
        sys.stderr.write("error! %s" % traceback.format_exc())
        html += '''<h3><span class="error">Sorry! An error occurred; it has been logged and will be investigated.<br/>
            However, it may take some days before the log is reviewed, so please contact John Lowe jblowe@berkeley.edu directly
            if you have even the <i>slightest</i> concern about getting this issue resolved.
            <br/>If there is a traceback below, please include the text!
            <br/>
            Finally, please record the time and what you were doing when this unfortunate event happened. Screenshots, are helpful, too.
            </span></h3><p/>''' + traceback.format_exc()

    elapsedtime = time.time() - elapsedtime

    writeInfo2log('end', form, config, elapsedtime)
    html += endhtml(form,config,elapsedtime)

    return html
