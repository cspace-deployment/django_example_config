#!/usr/bin/env /usr/bin/python
# -*- coding: UTF-8 -*-

import os
import copy

# for log
import csv
import json
import codecs
import ConfigParser

import time, datetime
import httplib, urllib2
import cgi
import re

import cswaSMBclient

from dirq.QueueSimple import QueueSimple
DIRQ = QueueSimple('/tmp/cswa')
WHEN2POST = 'now'

MAXLOCATIONS = 1000

try:
    import xml.etree.ElementTree as etree
    #print("running with ElementTree")
except ImportError:
    try:
        from lxml import etree
        #print("running with lxml.etree")
    except ImportError:
        try:
            # normal cElementTree install
            import cElementTree as etree
            #print("running with cElementTree")
        except ImportError:
            try:
                # normal ElementTree install
                import elementtree.ElementTree as etree
                #print("running with ElementTree")
            except ImportError:
                print("Failed to import ElementTree from any known place")

# the only other module: isolate postgres calls and connection
import cswaDB as cswaDB
import cswaConstants
import cswaGetAuthorityTree as cswaGetAuthorityTree
import cswaConceptutils as concept
from cswaHelpers import *

# updateactionlabel = config.get('info', 'updateactionlabel')
# updateType = config.get('info', 'updatetype')
# institution = config.get('info','institution')

#if not validateParameters(form, config): return


from common import cspace
from cspace_django_site.main import cspace_django_site

MAINCONFIG = cspace_django_site.getConfig()

def getConfig(request, action):
    try:
        # pretty hacky, let's improve the filename construction someday
        fileName = '.' + request.path.replace('toolbox/', 'toolbox/cfgs/') + '.cfg'
        config = ConfigParser.RawConfigParser()
        config.read(fileName)
        # test to see if it seems like it is really a config file
        updateType = config.get('info', 'updatetype')
        return config
    except:
        return False

def serverCheck(form, config):
    result = '<tr><td class="zcell">start server check</td><td class="zcell">' + time.strftime("%b %d %Y %H:%M:%S", time.localtime()) + "</td></tr>"

    elapsedtime = time.time()
    # do an sql search...
    result += '<tr><td class="zcell">SQL check</td><td class="zcell">' + cswaDB.testDB(config) + "</td></tr>"
    elapsedtime = time.time() - elapsedtime
    result += '<tr><td class="zcell">SQL time</td><td class="zcell">' + ('%8.2f' % elapsedtime) + " seconds</td></tr>"

    # if we are configured for barcodes, try that...
    try:
        config.get('files', 'cmdrfileprefix') + config.get('files', 'cmdrauditfile')
        try:
            elapsedtime = time.time()
            result += '<tr><td class="zcell">barcode audit file</td><td class="zcell">' + config.get('files', 'cmdrauditfile') + "</td></tr>"
            result += '<tr><td class="zcell">trying...</td><td class="zcell"> to write empty test files to commanderWatch directory</td></tr>'
            printers, selected, printerlist = cswaConstants.getPrinters(form)
            for printer in printerlist:
                result += ('<tr><td class="zcell">location labels @ %s</td><td class="zcell">' % printer[1]) + writeCommanderFile('test', printer[1], 'locationLabels', 'locations',  [], config) + "</td></tr>"
                result += ('<tr><td class="zcell">object labels @ %s</td><td class="zcell">' % printer[1]) + writeCommanderFile('test', printer[1], 'objectLabels', 'objects', [], config) + "</td></tr>"
            elapsedtime = time.time() - elapsedtime
            result += '<tr><td class="zcell">barcode check time</td><td class="zcell">' + ('%8.2f' % elapsedtime) + " seconds</td></tr>"
        except:
            result += '<tr><td class="zcell">barcode functionality check</td><td class="zcell"><span class="error">FAILED.</span></td></tr>'
    except:
        result += '<tr><td class="zcell">barcode functionality check</td><td class="zcell">skipped, not configured in config file.</td></tr>'

    elapsedtime = time.time()
    # rest check...
    elapsedtime = time.time() - elapsedtime
    result += '<tr><td class="zcell">REST check</td><td class="zcell">Not ready yet.</td></tr>'
    #result += "<tr><td class="zcell">REST check</td><td class="zcell">" + ('%8.2f' % elapsedtime) + " seconds</td></tr>"

    result += '<tr><td class="zcell">end server check</td><td class="zcell">' + time.strftime("%b %d %Y %H:%M:%S", time.localtime()) + "</td></tr>"
    result += '''<tr><td colspan="2"></td></tr>'''

    return '''<table><tbody><tr><td><h3>Server Status Check</h3></td></tr>''' + result + '''</tbody></table>'''


def makeGroup(form,config):
    pass


def listAuthorities(authority, primarytype, authItem, config, form, displaytype):
    if authItem == None or authItem == '': return
    rows = cswaGetAuthorityTree.getAuthority(authority, primarytype, authItem, config.get('connect', 'connect_string'))

    hasDups, html = listSearchResults(authority, config, displaytype, form, rows)

    return rows


def doComplexSearch(form, config, displaytype):
    #if not validateParameters(form,config): return
    listAuthorities('taxon', 'TaxonTenant35', form.get("ut.taxon"), config, form, displaytype)
    listAuthorities('locations', 'Locationitem', form.get("lo.location1"), config, form, displaytype)
    listAuthorities('places', 'Placeitem', form.get("px.place"), config, form, displaytype)
    #listAuthorities('taxon',     'TaxonTenant35',  form.get("ob.objectnumber"),config, form, displaytype)
    #listAuthorities('concepts',  'TaxonTenant35',  form.get("cx.concept"),     config, form, displaytype)

    getTableFooter(config, displaytype, '')


def doLocationSearch(form, config, displaytype):
    html = ''

    valid, error = validateParameters(form, config)
    if not valid: return html + error
    updateType = config.get('info', 'updatetype')

    try:
        #If barcode print, assume empty end location is start location
        if updateType == "barcodeprint":
            if form.get("lo.location2"):
                rows = cswaDB.getloclist('range', form.get("lo.location1"), form.get("lo.location2"), 500, config)
            else:
                rows = cswaDB.getloclist('range', form.get("lo.location1"), form.get("lo.location1"), 500, config)
        else:
            rows = cswaDB.getloclist('range', form.get("lo.location1"), form.get("lo.location2"), MAXLOCATIONS, config)
    except:
        raise

    hasDups, html = listSearchResults('locations', config, displaytype, form, rows)

    if hasDups:
        html += getTableFooter(config, 'error', 'Please eliminate duplicates and try again!')
        return
    if len(rows) != 0: html += getTableFooter(config, displaytype, '')
    return html


def doProcedureSearch(form, config, displaytype):
    html = ''

    valid, error = validateParameters(form, config)
    if not valid: return html + error

    updateType = config.get('info', 'updatetype')
    institution = config.get('info','institution')
    updateactionlabel = config.get('info', 'updateactionlabel')

    if updateType == 'intake':
        crate = verifyLocation(form.get("lo.crate"), form, config)
        toLocation = verifyLocation(form.get("lo.location1"), form, config)

        if str(form.get("lo.crate")) != '' and crate == '':
            html += '<span style="color:red;">Crate is not valid! Sorry!</span><br/>'
        if toLocation == '':
            html += '<span style="color:red;">Destination is not valid! Sorry!</span><br/>'
        if (str(form.get("lo.crate")) != '' and crate == '') or toLocation == '':
            return

        toRefname = cswaDB.getrefname('locations_common', toLocation, config)
        toCrate = cswaDB.getrefname('locations_common', crate, config)

    try:
        rows = cswaDB.getobjlist('range', form.get("ob.objno1"), form.get("ob.objno2"), 500, config)
    except:
        raise

    if len(rows) == 0:
        html += '<span style="color:red;">No objects in this range! Sorry!</span>'
    else:
        totalobjects = 0
        if updateType == 'objinfo':
            html += cswaConstants.infoHeaders(form.get('fieldset'))
        else:
            html += cswaConstants.getHeader(updateType,institution)
        for r in rows:
            totalobjects += 1
            html += formatRow({'rowtype': updateType, 'data': r}, form, config)

        html += '\n</table><table width="100%"'
        html += """<tr><td align="center" colspan="3">"""
        msg = "Caution: clicking on the button at left will update <b>ALL %s objects</b> shown on this page!" % totalobjects
        html += '''<input type="submit" class="save" value="''' + updateactionlabel + '''" name="action"></td><td  colspan="3">%s</td></tr>''' % msg
        html += "\n</table>"

        if updateType == 'moveobject':
            html += '<input type="hidden" name="toRefname" value="%s">' % toRefname
            html += '<input type="hidden" name="toCrate" value="%s">' % toCrate
            html += '<input type="hidden" name="toLocAndCrate" value="%s: %s">' % (toLocation, crate)

    return html

def doObjectSearch(form, config, displaytype):
    html = ''

    valid, error = validateParameters(form, config)
    if not valid: return html + error

    if form.get('ob.objno1') == '':
        html += '<h3>Please enter a starting object number!</h3>'
        return

    updateType = config.get('info', 'updatetype')
    institution = config.get('info','institution')
    updateactionlabel = config.get('info', 'updateactionlabel')

    if updateType == 'moveobject':
        crate = verifyLocation(form.get("lo.crate"), form, config)
        toLocation = verifyLocation(form.get("lo.location1"), form, config)

        if str(form.get("lo.crate")) != '' and crate == '':
            html += '<span style="color:red;">Crate is not valid! Sorry!</span><br/>'
        if toLocation == '':
            html += '<span style="color:red;">Destination is not valid! Sorry!</span><br/>'
        if (str(form.get("lo.crate")) != '' and crate == '') or toLocation == '':
            return

        toRefname = cswaDB.getrefname('locations_common', toLocation, config)
        toCrate = cswaDB.getrefname('locations_common', crate, config)

    try:
        rows = cswaDB.getobjlist('range', form.get("ob.objno1"), form.get("ob.objno2"), 500, config)
    except:
        raise

    if len(rows) == 0:
        html += '<span style="color:red;">No objects in this range! Sorry!</span>'
    else:
        totalobjects = 0
        if updateType == 'objinfo':
            html += cswaConstants.infoHeaders(form.get('fieldset'))
        else:
            html += cswaConstants.getHeader(updateType,institution)
        for r in rows:
            totalobjects += 1
            html += formatRow({'rowtype': updateType, 'data': r}, form, config)

        html += '\n</table><table width="100%"'
        html += """<tr><td align="center" colspan="3">"""
        msg = "Caution: clicking on the button at left will update <b>ALL %s objects</b> shown on this page!" % totalobjects
        html += '''<input type="submit" class="save" value="''' + updateactionlabel + '''" name="action"></td><td  colspan="3">%s</td></tr>''' % msg
        html += "\n</table>"

        if updateType == 'moveobject':
            html += '<input type="hidden" name="toRefname" value="%s">' % toRefname
            html += '<input type="hidden" name="toCrate" value="%s">' % toCrate
            html += '<input type="hidden" name="toLocAndCrate" value="%s: %s">' % (toLocation, crate)

    return html

def doOjectRangeSearch(form, config, displaytype=''):
    html = ''

    valid, error = validateParameters(form, config)
    if not valid: return html + error

    updateType = config.get('info', 'updatetype')
    updateactionlabel = config.get('info', 'updateactionlabel')

    try:
        if form.get('ob.objno2'):
            objs = cswaDB.getobjlist('range', form.get("ob.objno1"), form.get("ob.objno2"), 1000, config)
        else:
            objs = cswaDB.getobjlist('range', form.get("ob.objno1"), form.get("ob.objno1"), 1000, config)
    except:
        raise
    html += """
    <table><tr>
    <th>Object</th>
    <th>Count</th>
    <th>Object Name</th>
    <th>Culture</th>
    <th>Collection Place</th>
    <th>Ethnographic File Code</th>
    </tr>"""
    for o in objs:
        html += '''<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>''' % (o[3], o[5], o[4], o[7], o[6], o[9])

    html += """<tr><td align="center" colspan="6"></td></tr>"""
    html += """<tr><td align="center" colspan="6"><b>%s objects</b></td></tr>""" % len(objs)
    html += """<tr><td align="center" colspan="6">"""
    html += '''<input type="submit" class="save" value="''' + updateactionlabel + '''" name="action"></td></tr>'''

    return html

def listSearchResults(authority, config, displaytype, form, rows):
    html = ''
    updateType = config.get('info', 'updatetype')
    institution = config.get('info','institution')
    hasDups = False

    if not rows: rows = []
    rows.sort()
    rowcount = len(rows)

    label = authority
    if label[-1] == 's' and rowcount == 1: label = label[:-1]
    if label == 'taxon' and rowcount > 1: label = 'taxa'

    if displaytype == 'silent':
        html += """<table>"""
    elif displaytype == 'select':
        html += """<div style="float:left; width: 300px;">%s %s in this range</th>""" % (rowcount, label)
    else:
        if updateType == 'barcodeprint':
            rows.reverse()
            count = 0
            objectsHandled = []
            for r in rows:
                objects = cswaDB.getlocations(r[0], '', 1, config, updateType,institution)
                for o in objects:
                    if o[3] + o[4] in objectsHandled:
                        objects.remove(o)
                    else:
                        objectsHandled.append(o[3] + o[4])
                count += len(objects)
            html += """
    <table width="100%%">
    <tr>
      <th>%s %s and %s objects in this range</th>
    </tr>""" % (rowcount, label, count)
        else:
            html += """
    <table width="100%%">
    <tr>
      <th>%s %s in this range</th>
    </tr>""" % (rowcount, label)

    if rowcount == 0:
        html += "</table>"
        return hasDups, html

    if displaytype == 'select':
        html += """<li><input type="checkbox" name="select-%s" id="select-%s" checked/> select all</li>""" % (
            authority, authority)

    if displaytype == 'list' or displaytype == 'select':
        rowtype = 'location'
        if displaytype == 'select': rowtype = 'select'
        duplicates = []
        for r in rows:
            #html += "<b>r = </b>",r
            if r[1] in duplicates:
                hasDups = True
                #r.append('')
                # r.append('Duplicate!')
            else:
                #r.append('')
                #duplicates.append(r[1])
                pass
            html += formatRow({'boxtype': authority, 'rowtype': rowtype, 'data': r}, form, config)

    elif displaytype == 'nolist':
        label = authority
        if label[-1] == 's': label = label[:-1]
        if rowcount == 1:
            html += '<tr><td class="authority">%s</td></tr>' % (rows[0][0])
        else:
            html += '<tr><th>first %s</th><td class="authority">%s</td></tr>' % (label, rows[0][0])
            html += '<tr><th>last %s</th><td class="authority">%s</td></tr>' % (label, rows[-1][0])

    if displaytype == 'select':
        html += "\n</div>"
    else:
        html += "</table>"
        #html += """<input type="hidden" name="count" value="%s">""" % rowcount

    return hasDups, html


def doGroupSearch(form, config, displaytype):
    html = ''

    valid, error = validateParameters(form, config)
    if not valid: return html + error

    updateType = config.get('info', 'updatetype')

    if form.get('gr.group') == '':
        html += '<h3>Please enter group identifier!</h3>'
        return

    if updateType == "barcodeprint":
        updateType = 'packinglist'
    else:
        updateType = 'objinfo'
    institution = config.get('info','institution')
    updateactionlabel = config.get('info', 'updateactionlabel')

    try:
        #sys.stderr.write('group: %s\n' % form.get("gr.group"))
        rows = cswaDB.getgrouplist(form.get("gr.group"), 3000, config)
        #sys.stderr.write('group result: %s\n' % len(rows))
    except:
        #sys.stderr.write('group: %s\n' % form.get("gr.group"))
        raise
    #[sys.stderr.write('group member : %s\n' % x[2]) for x in rows]

    if len(rows) == 0:
        html += '<span style="color:red;">No objects in this group! Sorry!</span>'
    else:
        totalobjects = 0
        if updateType == 'objinfo':
            html += cswaConstants.infoHeaders(form.get('fieldset'))
        else:
            html += cswaConstants.getHeader(updateType,institution)
        for r in rows:
            totalobjects += 1
            html += formatRow({'rowtype': updateType, 'data': r}, form, config)

        html += '\n</table><table width="100%"'
        html += """<tr><td align="center" colspan="3">"""
        msg = "Caution: clicking on the button at left will update <b>ALL %s objects</b> shown on this page!" % totalobjects
        html += '''<input type="submit" class="save" value="''' + updateactionlabel + '''" name="action"></td><td  colspan="3">%s</td></tr>''' % msg
        html += "\n</table>"

    return html

def doEnumerateObjects(form, config):
    html = ''

    updateactionlabel = config.get('info', 'updateactionlabel')
    updateType = config.get('info', 'updatetype')
    institution = config.get('info','institution')

    valid, error = validateParameters(form, config)
    if not valid: return html + error

    try:
        locationList = cswaDB.getloclist('range', form.get("lo.location1"), form.get("lo.location2"), MAXLOCATIONS,
                                         config)
    except:
        raise

    rowcount = len(locationList)

    if rowcount == 0:
        html += '<h2>No locations in this range!</h2>'
        return

    if updateType == 'keyinfo' or updateType == 'objinfo':
        html += cswaConstants.infoHeaders(form.get('fieldset'))
    else:
        html += cswaConstants.getHeader(updateType,institution)
    totalobjects = 0
    totallocations = 0
    for l in locationList:

        try:
            objects = cswaDB.getlocations(l[0], '', 1, config, updateType,institution)
        except:
            raise

        rowcount = len(objects)
        locations = {}
        if rowcount == 0:
            locationheader = formatRow({'rowtype': 'subheader', 'data': l}, form, config)
            locations[locationheader] = ['<tr><td colspan="3">No objects found at this location.</td></tr>']
        for r in objects:
            locationheader = formatRow({'rowtype': 'subheader', 'data': r}, form, config)
            if locationheader in locations:
                pass
            else:
                locations[locationheader] = []
                totallocations += 1

            totalobjects += 1
            locations[locationheader].append(formatRow({'rowtype': updateType, 'data': r}, form, config))

        locs = locations.keys()
        locs.sort()
        for header in locs:
            html += header
            html += '\n'.join(locations[header])


    html += "\n</table>\n"
    if totalobjects == 0:
        pass
    else:
        html += ""
        html += '\n<table width="100%">\n'
        html += """<tr><td align="center" colspan="3">"""
        if updateType == 'keyinfo' or updateType == 'objinfo':
            msg = "Caution: clicking on the button at left will revise the above fields for <b>ALL %s objects</b> shown in these %s locations!" % (
                totalobjects, totallocations)
        else:
            msg = "Caution: clicking on the button at left will change the " + updateType + " of <b>ALL %s objects</b> shown in these %s locations!" % (
                totalobjects, totallocations)
        html += '''<input type="submit" class="save" value="''' + updateactionlabel + '''" name="action"></td><td  colspan="4">%s</td></tr>''' % msg
        html += "\n</table>"

    return html


def verifyLocation(loc, form, config):
    location = cswaDB.getloclist('exact', loc, '', 1, config)
    if location == [] : return
    if loc == location[0][0]:
        return loc
    else:
        return ''

def doCheckMove(form, config):
    html = ''

    updateactionlabel = config.get('info', 'updateactionlabel')
    updateType = config.get('info', 'updatetype')
    institution = config.get('info','institution')

    valid, error = validateParameters(form, config)
    if not valid: return html + error

    crate = verifyLocation(form.get("lo.crate"), form, config)
    fromLocation = verifyLocation(form.get("lo.location1"), form, config)
    toLocation = verifyLocation(form.get("lo.location2"), form, config)

    toRefname = cswaDB.getrefname('locations_common', toLocation, config)

    #sys.stderr.write('%-13s:: %-18s:: %s\n' % (updateType, 'toRefName', toRefname))

    # DEBUG
    #html += '<table cellpadding="8px" border="1">'
    #html += '<tr><td>%s</td><td>%s</td></tr>' % ('From',fromLocation)
    #html += '<tr><td>%s</td><td>%s</td></tr>' % ('Crate',crate)
    #html += '<tr><td>%s</td><td>%s</td></tr>' % ('To',toLocation)
    #html += '</table>'

    if crate == '':
        html += '<span style="color:red;">Crate is not valid! Sorry!</span><br/>'
    if fromLocation == '':
        html += '<span style="color:red;">From location is not valid! Sorry!</span><br/>'
    if toLocation == '':
        html += '<span style="color:red;">To location is not valid! Sorry!</span><br/>'
    if crate == '' or fromLocation == '' or toLocation == '':
        return

    try:
        # NB: the movecrate webapp uses the inventory query...naturally!
        objects = cswaDB.getlocations(form.get("lo.location1"), '', 1, config, 'inventory',institution)
    except:
        raise

    locations = {}
    if len(objects) == 0:
        html += '<span style="color:red;">No objects found at this location! Sorry!</span>'
        return

    totalobjects = 0
    totallocations = 0

    #sys.stderr.write('%-13s:: %s :: %-18s:: %s\n' % (updateType, crate, 'objects', len(objects)))
    for r in objects:
        if r[15] != crate: # skip if this is not the crate we want
            continue
        #sys.stderr.write('%-13s:: %-18s:: %s\n' % (updateType,  r[15],  r[0]))
        locationheader = formatRow({'rowtype': 'subheader', 'data': r}, form, config)
        if locationheader in locations:
            pass
        else:
            locations[locationheader] = []
            totallocations += 1

        totalobjects += 1
        locations[locationheader].append(formatRow({'rowtype': 'inventory', 'data': r}, form, config))

    locs = locations.keys()
    locs.sort()

    if len(locs) == 0:
        html += '<span style="color:red;">Did not find this crate at this location! Sorry!</span>'
        return

    html += cswaConstants.getHeader(updateType,institution)
    for header in locs:
        html += header
        html += '\n'.join(locations[header])

    html += """<tr><td align="center" colspan="6"><td></tr>"""
    html += """<tr><td align="center" colspan="3">"""
    msg = "Caution: clicking on the button at left will move <b>ALL %s objects</b> shown in this crate!" % totalobjects
    html += '''<input type="submit" class="save" value="''' + updateactionlabel + '''" name="action"></td><td  colspan="3">%s</td></tr>''' % msg

    html += "\n</table>"
    html += '<input type="hidden" name="toRefname" value="%s">' % toRefname
    html += '<input type="hidden" name="toLocAndCrate" value="%s: %s">' % (toLocation, crate)

    return html


def doCheckGroupMove(form, config):
    html = ''

    updateactionlabel = config.get('info', 'updateactionlabel')
    #updateType = config.get('info', 'updatetype')
    institution = config.get('info', 'institution')

    if form.get('gr.group') == '':
        html += '<h3>Please enter group identifier!</h3>'
        return

    toLocation = verifyLocation(form.get("lo.location"), form, config)
    toRefname = cswaDB.getrefname('locations_common', toLocation, config)

    if toLocation is None:
        html += '<h3>Please enter a valid storage location!</h3>'
        return

    updateType = 'powermove'
    institution = config.get('info','institution')
    updateactionlabel = config.get('info', 'updateactionlabel')

    try:
        objects = cswaDB.getgrouplist(form.get("gr.group"), 3000, config)
    except:
        raise

    locations = []
    if len(objects) == 0:
        html += '<span style="color:red;">No objects found for this group! Sorry!</span>'
        return

    totalobjects = 0

    # sys.stderr.write('%-13s:: %s :: %-18s:: %s\n' % (updateType, crate, 'objects', len(objects)))
    for r in objects:
        # sys.stderr.write('%-13s:: %-18s:: %s\n' % (updateType,  r[3],  r[0]))
        # swap these two elements: getgrouplist and getlocations return slightly different sets.
        x = r[4]
        r[4] = r[5]
        r[5] = x
        totalobjects += 1
        locations.append(formatRow({'rowtype': 'powermove', 'data': r}, form, config))

    html += cswaConstants.getHeader('powermove', institution)
    html += """<tr><td align="center" colspan="6"><td></tr>"""
    html += '\n'.join(locations)
    html += """<tr><td align="center" colspan="6"><td></tr>"""
    html += """<tr><td align="center" colspan="3">"""
    msg = "Caution: clicking on the button at left will move <b>ALL %s objects</b> shown for this group!" % totalobjects
    html += '''<input type="submit" class="save" value="''' + updateactionlabel + '''" name="action"></td><td  colspan="3">%s</td></tr>''' % msg

    html += "\n</table>"
    html += '<input type="hidden" name="toRefname" value="%s">' % toRefname
    html += '<input type="hidden" name="toLocAndCrate" value="%s">' % (toLocation)
    html += '<input type="hidden" name="toCrate" value="%s">' % ''

    return html


def doCheckPowerMove(form, config):
    html = ''

    updateactionlabel = config.get('info', 'updateactionlabel')
    updateType = config.get('info', 'updatetype')
    institution = config.get('info','institution')

    valid, error = validateParameters(form, config)
    if not valid: return html + error

    crate1 = verifyLocation(form.get("lo.crate1"), form, config)
    crate2 = verifyLocation(form.get("lo.crate2"), form, config)

    if crate1 == '':
        html += '<span style="color:red;">From Crate is not valid! Sorry!</span><br/>'
    if crate2 == '':
        html += '<span style="color:red;">To Crate is not valid! Sorry!</span><br/>'

    fromLocation = verifyLocation(form.get("lo.location1"), form, config)
    toLocation = verifyLocation(form.get("lo.location2"), form, config)

    if fromLocation == '':
        html += '<span style="color:red;">From location is not valid! Sorry!</span><br/>'
    if toLocation == '':
        html += '<span style="color:red;">To location is not valid! Sorry!</span><br/>'
    if fromLocation == '' or toLocation == '':
        return

    toLocRefname = cswaDB.getrefname('locations_common', toLocation, config)
    toCrateRefname = cswaDB.getrefname('locations_common', crate2, config)
    fromRefname = cswaDB.getrefname('locations_common', fromLocation, config)

    #sys.stderr.write('%-13s:: %-18s:: %s\n' % (updateType, 'toRefName', toRefname))

    # DEBUG
    #html += '<table cellpadding="8px" border="1">'
    #html += '<tr><td>%s</td><td>%s</td></tr>' % ('From',fromLocation)
    #html += '<tr><td>%s</td><td>%s</td></tr>' % ('Crate',crate)
    #html += '<tr><td>%s</td><td>%s</td></tr>' % ('To',toLocation)
    #html += '</table>'

    try:
        # NB: the movecrate webapp uses the inventory query...naturally!
        objects = cswaDB.getlocations(form.get("lo.location1"), '', 1, config, 'inventory',institution)
    except:
        raise

    locations = {}
    if len(objects) == 0:
        html += '<span style="color:red;">No objects found at this location! Sorry!</span>'
        return

    totalobjects = 0
    totallocations = 0

    #sys.stderr.write('%-13s:: %s :: %-18s:: %s\n' % (updateType, crate, 'objects', len(objects)))
    for r in objects:
        if r[15] != crate1 and crate1 != '': # skip if this is not the crate we want
                continue
        #sys.stderr.write('%-13s:: %-18s:: %s\n' % (updateType,  r[15],  r[0]))
        locationheader = formatRow({'rowtype': 'subheader', 'data': r}, form, config)
        if locationheader in locations:
            pass
        else:
            locations[locationheader] = []
            totallocations += 1

        totalobjects += 1
        locations[locationheader].append(formatRow({'rowtype': 'powermove', 'data': r}, form, config))

    locs = locations.keys()
    locs.sort()

    if len(locs) == 0:
        html += '<span style="color:red;">Did not find this crate at this location! Sorry!</span>'
        return

    html += cswaConstants.getHeader(updateType,institution)
    for header in locs:
        html += header
        html += '\n'.join(locations[header])

    html += """<tr><td align="center" colspan="6"><td></tr>"""
    html += """<tr><td align="center" colspan="3">"""
    msg = "Caution: clicking on the button at left will move <b>ALL %s objects</b> shown in this crate!" % totalobjects
    html += '''<input type="submit" class="save" value="''' + updateactionlabel + '''" name="action"></td><td  colspan="3">%s</td></tr>''' % msg

    html += "\n</table>"
    if crate2 is None: crate2 = ''
    html += '<input type="hidden" name="toRefname" value="%s">' % toLocRefname
    html += '<input type="hidden" name="toLocAndCrate" value="%s: %s">' % (toLocation, crate2)
    html += '<input type="hidden" name="toCrate" value="%s">' % toCrateRefname

    return html


def doBulkEdit(form, config):
    html = ''

    valid, error = validateParameters(form, config)
    if not valid: return html + error

    updateType = config.get('info', 'updatetype')
    updateactionlabel = config.get('info', 'updateactionlabel')

    try:
        if form.get('ob.objno2'):
            objs = cswaDB.getobjlist('range', form.get("ob.objno1"), form.get("ob.objno2"), 3000, config)
        else:
            objs = cswaDB.getobjlist('range', form.get("ob.objno1"), form.get("ob.objno1"), 3000, config)
    except:
        objs = []


    CSIDs = []
    fieldset = form.get('fieldset')
    for row in objs:
        CSIDs.append(row[8])

    refNames2find = {}

    index = 'user'
    if fieldset == 'namedesc':
        pass
    elif fieldset == 'registration':
        if not refNames2find.has_key(form.get('ant.' + index)):
            refNames2find[form.get('ant.' + index)] = cswaDB.getrefname('pahmaaltnumgroup_type', form.get('ant.' + index), config)
        if not refNames2find.has_key(form.get('pc.' + index)):
            refNames2find[form.get('pc.' + index)] = cswaDB.getrefname('collectionobjects_common_fieldcollectors', form.get('pc.' + index), config)
        if not refNames2find.has_key(form.get('pd.' + index)):
            refNames2find[form.get('pd.' + index)] = cswaDB.getrefname('acquisitions_common_owners', form.get('pd.' + index), config)
    elif fieldset == 'keyinfo':
        if not refNames2find.has_key(form.get('cp.' + index)):
            refNames2find[form.get('cp.' + index)] = cswaDB.getrefname('places_common', form.get('cp.' + index), config)
        if not refNames2find.has_key(form.get('cg.' + index)):
            refNames2find[form.get('cg.' + index)] = cswaDB.getrefname('concepts_common', form.get('cg.' + index), config)
        if not refNames2find.has_key(form.get('fc.' + index)):
            refNames2find[form.get('fc.' + index)] = cswaDB.getrefname('concepts_common', form.get('fc.' + index), config)
    elif fieldset == 'hsrinfo':
        if not refNames2find.has_key(form.get('cp.' + index)):
            refNames2find[form.get('cp.' + index)] = cswaDB.getrefname('places_common', form.get('cp.' + index), config)
    elif fieldset == 'objtypecm':
        if not refNames2find.has_key(form.get('cp.' + index)):
            refNames2find[form.get('cp.' + index)] = cswaDB.getrefname('places_common', form.get('cp.' + index), config)
    else:
        pass
        #error! fieldset not set!

    doTheUpdate(CSIDs, form, config, fieldset, refNames2find)



def doBulkEditForm(form, config, displaytype):
    html = ''

    valid, error = validateParameters(form, config)
    if not valid: return html + error

    updateType = config.get('info', 'updatetype')
    updateactionlabel = config.get('info', 'updateactionlabel')

    try:
        if form.get('ob.objno2'):
            objs = cswaDB.getobjlist('range', form.get("ob.objno1"), form.get("ob.objno2"), 3000, config)
        else:
            objs = cswaDB.getobjlist('range', form.get("ob.objno1"), form.get("ob.objno1"), 3000, config)
    except:
        objs = []

    totalobjects = len(objs)

    if totalobjects == 0:
        html += '<span style="color:red;">No objects found! Sorry!</span>'
        return

    html += '''<table width="100%" cellpadding="8px"><tbody><tr class="smallheader">
      <td width="250px">Field</td>
      <td>Value to Set</td></tr>'''

    html += formatInfoReviewForm(form)

    html += '</table>'
    html += '<table>'

    msg = "Caution: clicking on the button at left will update <b>ALL %s objects</b> in this range!" % totalobjects
    html += """<tr><td align="center" colspan="3"></tr>"""
    html += """<tr><td align="center" colspan="2">"""
    html += '''<input type="submit" class="save" value="''' + updateactionlabel + '''" name="action"></td><td  colspan="1">%s</td></tr>''' % msg


    html += '</table>'
    html += ""

    return html


def doCreateObjects(form, config):
    html = ''

    # html += form
    #if not validateParameters(form, config): return

    updateType = config.get('info', 'updatetype')
    updateactionlabel = config.get('info', 'updateactionlabel')
    msgs = []

    html += '''<table width="100%" cellpadding="8px"><tbody><tr class="smallheader">
      <td>Item</td><td>Value</td>'''

    year, msg = getints('create.year', form)
    if msg != '': msgs.append(msg)
    accession, msg = getints('create.accession', form)
    if msg != '': msgs.append(msg)
    sequence, msg = getints('create.sequence', form)
    if msg != '': msgs.append(msg)
    count, msg = getints('create.count', form)
    if msg != '': msgs.append(msg)

    try:
        startsortobject = '%0.10d.%0.10d.%0.10d' % (year, accession, sequence)
        startobject = '%s.%s.%s' % (year, accession, sequence)
    except:
        startobject = 'invalid'
        msgs.append('start object value invalid')

    try:
        endsortobject = '%0.10d.%0.10d.%0.10d' % (year, accession, sequence + count - 1)
        endobject = '%s.%s.%s' % (year, accession, sequence + count - 1)
    except:
        endobject = 'invalid'
        msgs.append('end object value invalid')

    try:
        objs = cswaDB.getlistofobjects('range', startsortobject, endsortobject, 100, config)
        totalobjects = len(objs)
        if totalobjects != 0:
            msgs.append('there are already %s objects in this range!' % totalobjects)
            msgs.append('(%s to %s)' % (startobject, endobject))
            for o in objs:
                msgs.append(o[0])
    except:
        msgs.append('problem checking object range')
        totalobjects = -1

    if count > 100:
        msgs.append('Maximum objects you can create at one time is 100.')
        msgs.append('Consider breaking your work into chunks of 100.')

    if len(msgs) == 0:
        html += "<tr><td>%s</td><td>%s</td></tr>" % ('first object', startobject)
        html += "<tr><td>%s</td><td>%s</td></tr>" % ('last object', endobject)
        html += "<tr><td>%s</td><td>%s</td></tr>" % ('objects requested', count)

        if form.get('action') == config.get('info', 'updateactionlabel'):
            # create objects here
            for seq in range(count):
                objectNumber = '%s.%s.%s' % (year, accession, sequence + seq)
                sortableobjectnumber = '%0.10d.%0.10d.%0.10d' % (year, accession, sequence + seq)
                objectinfo = {'objectNumber': objectNumber}
                objectinfo['sortableObjectNumber'] = sortableobjectnumber
                message,csid = createObject(objectinfo, config, form)
                html += "<tr><td>%s</td><td>%s</td></tr>" % (objectNumber, csid)
            html += "<tr><td>%s</td><td>%s</td></tr>" % ('created objects', count)
        else:
            # list objects to be created
            msg = "Caution: clicking on the button at left will create <b> %s empty objects</b>!" % count
            html += """<tr><td align="center" colspan="3"></tr>"""
            html += """<tr><td align="center" colspan="2">"""
            html += '''<input type="submit" class="save" value="''' + updateactionlabel + '''" name="action"></td><td colspan="1">%s</td></tr>''' % msg

    else:
        for m in msgs:
            html += '<tr><td class="error">%s</td><td></td></tr>' % m

    html += '</table>'
    html += ""

    return html

def doSetupIntake(form, config):
    html = ''

    updateType = config.get('info', 'updatetype')
    institution = config.get('info','institution')
    updateactionlabel = config.get('info', 'updateactionlabel')

    html += '<table width="100%">'
    html += formatRow({'rowtype': 'subheader', 'data': ['Intake Values']}, form, config)

    html += cswaConstants.getHeader('intakeValues',institution)

    # get numbobjects
    numobjects = 1
    for i in cswaConstants.getIntakeFields('intake'):
        if i[2] == 'numobjects':
            try:
                numobjects = int(form.get(i[2]))
            except:
                pass

    for i,box in enumerate(cswaConstants.getIntakeFields('intake')):
        if box[2] == 'dummy':
            continue
        if box[4] == 'fixed':
            if box[2] == 'tr':
                if numobjects == 1:
                    objectrange = '1'
                else:
                    objectrange = '1-' + str(numobjects)
                computedresult = 'TR. ' + form.get(box[2]) + '.14.' + objectrange
                html += '<tr><th class="zcell">%s</th><td>%s</td></tr>' % (box[0],computedresult)
            else:
                html += '<tr><th class="zcell">%s</th><td>%s</td></tr>' % (box[0],form.get(box[2]))
        else:
            html += '<tr><th class="zcell">%s</th><td>%s</td></tr>' % (box[0],form.get(box[2]))

    html += formatRow({'rowtype': 'subheader', 'data': ['Basic Collection Object Info']}, form, config)

    objectDescriptions = cswaConstants.getIntakeFields('objects')

    #html += "<tr>"
    #for o in objectDescriptions:
    #    html += '<th>%s</th>' % o[0]
    #html += "</tr>"

    for row in range(numobjects):
        html += '<tr>'
        for i,box in enumerate(objectDescriptions):
            if i % 5 == 0:
                html += "</tr><tr>"
            html += '''
            <td>%s<br/>
            <input id="%s.%s" class="xspan" type="%s" size="%s" name="%s.%s" value="%s"></td>
            ''' % (box[0],box[2],row,box[4],box[1],box[2],row,box[3])
        html += '</tr>'
        html += '<tr><td colspan="7"></td></tr>'

    html += '\n</table><table width="100%"'
    html += """<tr><td align="center" colspan="3">"""
    msg = "Caution: clicking on the button at left will create <b>intake and %s object records</b> as entered on this page!" % numobjects
    html += '''<input type="submit" class="save" value="''' + updateactionlabel + '''" name="action"></td><td  colspan="3">%s</td></tr>''' % msg
    html += "\n</table>"

    return html


def doCommitIntake(form, config):
    html = ''

    pass

def doUpdateKeyinfo(form, config):
    html = ''

    #html += form
    CSIDs = []
    fieldset = form.get('fieldset')
    for i in form:
        if 'csid.' in i:
            CSIDs.append(form.get(i))

    refNames2find = {}
    for row, csid in enumerate(CSIDs):

        index = csid # for now, the index is the csid
        if fieldset == 'namedesc':
            pass
        elif fieldset == 'registration':
            if not refNames2find.has_key(form.get('ant.' + index)):
                refNames2find[form.get('ant.' + index)] = cswaDB.getrefname('pahmaaltnumgroup_type', form.get('ant.' + index), config)
            if not refNames2find.has_key(form.get('pc.' + index)):
                refNames2find[form.get('pc.' + index)] = cswaDB.getrefname('collectionobjects_common_fieldcollectors', form.get('pc.' + index), config)
            if not refNames2find.has_key(form.get('pd.' + index)):
                refNames2find[form.get('pd.' + index)] = cswaDB.getrefname('acquisitions_common_owners', form.get('pd.' + index), config)
        elif fieldset == 'keyinfo':
            if not refNames2find.has_key(form.get('cp.' + index)):
                refNames2find[form.get('cp.' + index)] = cswaDB.getrefname('places_common', form.get('cp.' + index), config)
            if not refNames2find.has_key(form.get('cg.' + index)):
                refNames2find[form.get('cg.' + index)] = cswaDB.getrefname('concepts_common', form.get('cg.' + index), config)
            if not refNames2find.has_key(form.get('fc.' + index)):
                refNames2find[form.get('fc.' + index)] = cswaDB.getrefname('concepts_common', form.get('fc.' + index), config)
        elif fieldset == 'hsrinfo':
            if not refNames2find.has_key(form.get('cp.' + index)):
                refNames2find[form.get('cp.' + index)] = cswaDB.getrefname('places_common', form.get('cp.' + index), config)
        elif fieldset == 'objtypecm':
            if not refNames2find.has_key(form.get('cp.' + index)):
                refNames2find[form.get('cp.' + index)] = cswaDB.getrefname('places_common', form.get('cp.' + index), config)
        else:
            pass
            #error! fieldset not set!

    return doTheUpdate(CSIDs, form, config, fieldset, refNames2find)


def doTheUpdate(CSIDs, form, config, fieldset, refNames2find):
    html = ''

    updateType = config.get('info', 'updatetype')
    institution = config.get('info','institution')

    html += cswaConstants.getHeader('keyinfoResult',institution)

    #for r in refNames2find:
    #    html += '<tr><td>%s<td>%s<td>%s</tr>' % ('refname',refNames2find[r],r)
    #html += CSIDs

    numUpdated = 0
    for row, csid in enumerate(CSIDs):

        if updateType == 'bulkedit':
            index = 'user'
        else:
            index = csid
        updateItems = {}
        updateItems['objectCsid'] = csid
        updateItems['objectName'] = form.get('onm.' + index)
        #updateItems['objectNumber'] = form.get('oox.' + index)
        if fieldset == 'namedesc':
            updateItems['briefDescription'] = form.get('bdx.' + index)
        elif fieldset == 'registration':
            updateItems['pahmaAltNum'] = form.get('anm.' + index)
            updateItems['pahmaAltNumType'] = form.get('ant.' + index)
            updateItems['fieldCollector'] = refNames2find[form.get('pc.' + index)]
        elif fieldset == 'keyinfo':
            if form.get('ocn.' + index) != '':
                updateItems['objectCount'] = form.get('ocn.' + index)
            updateItems['pahmaFieldCollectionPlace'] = refNames2find[form.get('cp.' + index)]
            updateItems['assocPeople'] = refNames2find[form.get('cg.' + index)]
            updateItems['pahmaEthnographicFileCode'] = refNames2find[form.get('fc.' + index)]
        elif fieldset == 'hsrinfo':
            if form.get('ocn.' + index) != '':
                updateItems['objectCount'] = form.get('ocn.' + index)
            updateItems['inventoryCount'] = form.get('ctn.' + index)
            updateItems['pahmaFieldCollectionPlace'] = refNames2find[form.get('cp.' + index)]
            updateItems['briefDescription'] = form.get('bdx.' + index)
        elif fieldset == 'objtypecm':
            if form.get('ocn.' + index) != '':
                updateItems['objectCount'] = form.get('ocn.' + index)
            updateItems['collection'] = form.get('ot.' + index)
            updateItems['responsibleDepartment'] = form.get('cm.' + index)
            updateItems['pahmaFieldCollectionPlace'] = refNames2find[form.get('cp.' + index)]
        elif fieldset == 'placeanddate':
            updateItems['pahmaFieldLocVerbatim'] = form.get('vfcp.' + index)
            updateItems['pahmaFieldCollectionDate'] = form.get('cd.' + index)
        else:
            pass
            #error!

        for i in ('handlerRefName',):
            updateItems[i] = form.get(i)

        #html += updateItems
        msg = 'updated. '
        if fieldset == 'keyinfo':
            if updateItems['pahmaFieldCollectionPlace'] == '' and form.get('cp.' + index):
                if form.get('cp.' + index) == cswaDB.getCSIDDetail(config, index, 'fieldcollectionplace'):
                    pass
                else:
                    msg += '<span style="color:red;"> Field Collection Place: term "%s" not found, field not updated.</span>' % form.get('cp.' + index)
            if updateItems['assocPeople'] == '' and form.get('cg.' + index):
                if form.get('cg.' + index) == cswaDB.getCSIDDetail(config, index, 'assocpeoplegroup'):
                    pass
                else:
                    msg += '<span style="color:red;"> Cultural Group: term "%s" not found, field not updated.</span>' % form.get('cg.' + index)
            if updateItems['pahmaEthnographicFileCode'] == '' and form.get('fc.' + index):
                msg += '<span style="color:red;"> Ethnographic File Code: term "%s" not found, field not updated.</span>' % form.get('fc.' + index)
            if 'objectCount' in updateItems:
                try:
                    int(updateItems['objectCount'])
                    int(updateItems['objectCount'][0])
                except ValueError:
                    msg += '<span style="color:red;"> Object count: "%s" is not a valid number!</span>' % form.get('ocn.' + index)
                    del updateItems['objectCount']
        elif fieldset == 'registration':
            if updateItems['fieldCollector'] == '' and form.get('pc.' + index):
                msg += '<span style="color:red;"> Field Collector: term "%s" not found, field not updated.</span>' % form.get('pc.' + index)
        elif fieldset == 'hsrinfo':
            if updateItems['pahmaFieldCollectionPlace'] == '' and form.get('cp.' + index):
                if form.get('cp.' + index) == cswaDB.getCSIDDetail(config, index, 'fieldcollectionplace'):
                    pass
                else:
                    msg += '<span style="color:red;"> Field Collection Place: term "%s" not found, field not updated.</span>' % form.get('cp.' + index)
            if 'objectCount' in updateItems:
                try:
                    int(updateItems['objectCount'])
                    int(updateItems['objectCount'][0])
                except ValueError:
                    msg += '<span style="color:red;"> Object count: "%s" is not a valid number!</span>' % form.get('ocn.' + index)
                    del updateItems['objectCount']
        elif fieldset == 'objtypecm':
            if updateItems['pahmaFieldCollectionPlace'] == '' and form.get('cp.' + index):
                if form.get('cp.' + index) == cswaDB.getCSIDDetail(config, index, 'fieldcollectionplace'):
                    pass
                else:
                    msg += '<span style="color:red;"> Field Collection Place: term "%s" not found, field not updated.</span>' % form.get('cp.' + index)
            if 'objectCount' in updateItems:
                try:
                    int(updateItems['objectCount'])
                    int(updateItems['objectCount'][0])
                except ValueError:
                    msg += '<span style="color:red;"> Object count: "%s" is not a valid number!</span>' % form.get('ocn.' + index)
                    del updateItems['objectCount']
        elif fieldset == 'placeanddate':
            # msg += 'place and date'
            pass

        updateMsg = ''
        for item in updateItems.keys():
            if updateItems[item] == 'None' or updateItems[item] is None:
                if item in 'collection inventoryCount objectCount'.split(' '):
                    del updateItems[item]
                    #updateMsg += 'deleted %s <br/>' % item
                else:
                    updateItems[item] = ''
                    #updateMsg += 'eliminated %s <br/>' % item
            else:
                #updateMsg += 'kept %s, value: %s <br/>' % (item, updateItems[item])
                pass

        try:
            #pass
            updateMsg += updateKeyInfo(fieldset, updateItems, config, form)
            if updateMsg != '':
                msg += '<span style="color:red;">%s</span>' % updateMsg
            numUpdated += 1
        except:
            raise
            #msg += '<span style="color:red;">problem updating</span>'
        #html += ('<tr>' + (3 * '<td class="ncell">%s</td>') + '</tr>\n') % (
        #    updateItems['objectNumber'], updateItems['objectCsid'], msg)
        html += ('<tr>' + (3 * '<td class="ncell">%s</td>') + '</tr>\n') % ('',updateItems['objectCsid'], msg)
        # html += 'place %s' % updateItems['pahmaFieldCollectionPlace']

    html += "\n</table>"
    html += '<h4>%s of %s objects had key information updated</h4>' % (numUpdated, row + 1)

    return html


def doUpdateLocations(form, config):
    html = ''

    institution = config.get('info','institution')
    updateType = config.get('info', 'updatetype')
    #notlocated = config.get('info','notlocated')
    if institution == 'bampfa':
        notlocated = "urn:cspace:bampfa.cspace.berkeley.edu:locationauthorities:name(location):item:name(x781)'Not Located'"
    else:
        notlocated = "urn:cspace:bampfa.cspace.berkeley.edu:locationauthorities:name(location):item:name(sl23524)'Not located'"
    updateValues = [form.get(i) for i in form if 'r.' in i and not 'gr.' in i]

    # if reason is a refname (e.g. bampfa), extract just the displayname
    reason = form.get('reason')
    reason = re.sub(r"^urn:.*'(.*)'", r'\1', reason)

    Now = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    # Now = midnight local time for locations...
    # Now = datetime.datetime.utcnow().strftime("%Y-%m-%dT00:00:00Z")

    html += cswaConstants.getHeader('inventoryResult',institution)

    numUpdated = 0
    for row, object in enumerate(updateValues):

        updateItems = {}
        cells = object.split('|')
        updateItems['objectStatus'] = cells[0]
        updateItems['objectCsid'] = cells[1]
        updateItems['locationRefname'] = cells[2]
        updateItems['subjectCsid'] = '' # cells[3] is actually the csid of the movement record for the current location; the updated value gets inserted later
        updateItems['objectNumber'] = cells[4]
        updateItems['crate'] = cells[5]
        updateItems['inventoryNote'] = form.get('n.' + cells[4]) if form.get('n.' + cells[4]) else ''
        updateItems['locationDate'] = Now
        updateItems['computedSummary'] = updateItems['locationDate'][0:10] + (' (%s)' % reason)

        for i in ('handlerRefName', 'reason'):
            updateItems[i] = form.get(i)

        # ugh...this logic is in fact rather complicated...
        msg = 'location updated.'
        # if we are moving a crate, use the value of the toLocation's refname, which is stored hidden on the form.
        if updateType == 'movecrate':
            updateItems['locationRefname'] = form.get('toRefname')
            msg = 'crate moved to %s.' % form.get('toLocAndCrate')

        if updateType in ['moveobject', 'powermove', 'grpmove']:
            if updateItems['objectStatus'] == 'do not move':
                msg = "not moved."
            else:
                updateItems['locationRefname'] = form.get('toRefname')
                updateItems['crate'] = form.get('toCrate')
                msg = 'object moved to %s.' % form.get('toLocAndCrate')


        if updateItems['objectStatus'] == 'not found':
            updateItems['locationRefname'] = notlocated
            updateItems['crate'] = ''
            msg = "moved to 'Not Located'."
        try:
            if "not moved" in msg:
                pass
            else:
                updateLocations(updateItems, config, form)
                numUpdated += 1
        except:
            msg = '<span style="color:red;">location update failed!</span>'
        html += ('<tr>' + (4 * '<td class="ncell">%s</td>') + '</tr>\n') % (
            updateItems['objectNumber'], updateItems['objectStatus'], updateItems['inventoryNote'], msg)\

    html += "\n</table>"
    html += '<h4>%s of %s objects had key information updated</h4>' % (numUpdated, row + 1)

    return html


def doPackingList(form, config):
    html = ''

    updateactionlabel = config.get('info', 'updateactionlabel')
    updateType = config.get('info', 'updatetype')
    institution = config.get('info','institution')

    if form.get('groupbyculture') is not None:
        updateType = 'packinglistbyculture'

    valid, error = validateParameters(form, config)
    if not valid: return html + error

    place = form.get("cp.place")
    if place != None and place != '':
        places = cswaGetAuthorityTree.getAuthority('places',  'Placeitem', place,  config.get('connect', 'connect_string'))
        places = [p[0] for p in places]
    else:
        places = []

    #[sys.stderr.write('packing list place term: %s\n' % x) for x in places]
    try:
        locationList = cswaDB.getloclist('range', form.get("lo.location1"), form.get("lo.location2"), MAXLOCATIONS,
                                         config)
    except:
        raise

    rowcount = len(locationList)

    #[sys.stderr.write('packing list locations : %s\n' % x[0]) for x in locationList]

    if rowcount == 0:
        html += '<tr><td width="500px"><h2>No locations in this range!</h2></td></tr>'
        return

    html += cswaConstants.getHeader(updateType,institution)
    totalobjects = 0
    totallocations = 0
    locations = {}
    for l in locationList:

        try:
            objects = cswaDB.getlocations(l[0], '', 1, config, 'packinglist',institution)
        except:
            raise

        #[sys.stderr.write('packing list objects: %s\n' % x[3]) for x in objects]
        rowcount = len(objects)
        if rowcount == 0:
            if updateType != 'packinglistbyculture':
                locationheader = formatRow({'rowtype': 'subheader', 'data': l}, form, config)
                locations[locationheader] = ['<tr><td colspan="3">No objects found at this location.</td></tr>']
        for r in objects:
            if checkObject(places, r):
                totalobjects += 1
                if updateType == 'packinglistbyculture':
                    temp = copy.deepcopy(r)
                    cgrefname = r[11]
                    parentcount = 0
                    if cgrefname is not None:
                        parents = cswaDB.findparents(cgrefname, config)
                        #[sys.stderr.write('term: %s' % x) for x in parents]
                        if parents is None or len(parents) == 1:
                            subheader = 'zzzNo parent :: %s' % r[7]
                        else:
                            subheader = [term[0] for term in parents]
                            subheader = ' :: '.join(subheader)
                            parentcount = len(parents)
                    else:
                        subheader = 'zzzNo cultural group specified'
                        #sys.stderr.write('%s %s' % (str(r[7]), parentcount))
                    temp[0] = subheader
                    temp[7] = r[0]
                    r = temp
                    locationheader = formatRow({'rowtype': 'subheader', 'data': r}, form, config)
                else:
                    locationheader = formatRow({'rowtype': 'subheader', 'data': r}, form, config)
                if locationheader in locations:
                    pass
                else:
                    locations[locationheader] = []
                    totallocations += 1

                locations[locationheader].append(formatRow({'rowtype': updateType, 'data': r}, form, config))

    locs = locations.keys()
    locs.sort()
    for header in locs:
        html += header.replace('zzz', '')
        html += '\n'.join(locations[header])
        html += """<tr><td align="center" colspan="6">&nbsp;</tr>"""
    html += """<tr><td align="center" colspan="6"><td></tr>"""
    headingtypes = 'cultures' if updateType == 'packinglistbyculture' else 'including crates'
    html += """<tr><td align="center" colspan="6">Packing list completed. %s objects, %s locations, %s %s</td></tr>""" % (
        totalobjects, len(locationList), totallocations, headingtypes)
    html += "\n</table>"

    return html


def doAuthorityScan(form, config):
    html = ''

    updateactionlabel = config.get('info', 'updateactionlabel')
    updateType = config.get('info', 'updatetype')
    institution = config.get('info','institution')

    valid, error = validateParameters(form, config)
    if not valid: return html + error

    dead,rare,qualifier = setFilters(form)

    if updateType == 'locreport':
        Taxon = form.get("ut.taxon")
        if Taxon != None:
            Taxa = listAuthorities('taxon', 'TaxonTenant35', Taxon, config, form, 'list')
        else:
            Taxa = []
        tList = [t[0] for t in Taxa]
        column = 1

    elif updateType == 'holdings':
        Place = form.get("px.place")
        if Place != None:
            Places = listAuthorities('places', 'Placeitem', Place, config, form, 'silent')
        else:
            Places = []
        tList = [t[0] for t in Places]
        column = 5

    try:
        objects = cswaDB.getplants('', '', 1, config, 'getalltaxa', qualifier)
    except:
        raise

    rowcount = len(objects)

    if rowcount == 0:
        html += '<h2>No plants in this range!</h2>'
        return
        #else:
    #	showTaxon = Taxon
    #   if showTaxon == '' : showTaxon = 'all Taxons in this range'
    #   html += '<tr><td width="500px"><h2>%s locations will be listed for %s.</h2></td></tr>' % (rowcount,showTaxon)

    html += cswaConstants.getHeader(updateType,institution)
    counts = {}
    statistics = { 'Total items': 'totalobjects',
                   'Accessions': 0,
                   'Unique taxonomic names': 1,
                   'Unique species': 'species',
                   'Unique genera': 'genus'
    }
    for s in statistics.keys():
        counts[s] = cswaConstants.Counter()

    totalobjects = 0
    for t in objects:
        if t[column] in tList:
            if updateType in ['locreport','holdings'] and checkMembership(t[7], rare) and checkMembership(t[8], dead):
                if t[8] == 'true' or t[8] is None:
                    t[3] = "%s [%s]" % (t[13],t[12])
                else:
                    pass
                html += formatRow({'rowtype': updateType, 'data': t}, form, config)
                totalobjects += 1
                countStuff(statistics,counts,t,totalobjects)

    #html += '\n'.join(accessions)
    html += """</table>"""
    #html += """"""
    #html += """<table width="100%">"""
    #html += """<tr><td colspan="2"><b>Summary Statistics (experimental and unverified!)</b></tr>"""

    #for s in sorted(statistics.keys()):
    #   html += """<tr><th width=300px>%s</th><td>%s</td></tr>""" % (s, len(counts[s]))

    #html += """<tr><td align="center">Report completed.</td></tr>"""
    html += "\n</table>"

    return html


def downloadCsv(form, config):
    html = ''

    updateType = config.get('info', 'updateType')
    institution = config.get('info','institution')

    try:
        # create the HttpResponse object with the appropriate CSV header.
        response = HttpResponse(content_type='text/csv')
        filename = '%s_%s.csv' % (updateType, datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S"))
        response['Content-Disposition'] = 'attachment; filename="%s"' % filename
        #html += 'Content-type: application/octet-stream; charset=utf-8'
        writer = csv.writer(response, quoting=csv.QUOTE_ALL)
    except:
        html += 'Problem creating .csv file. Sorry!'
        return html

    if updateType == 'governmentholdings':
        try:
            query = cswaDB.getDisplayName(config, form.get('agency'))[0]
            hostname = config.get('connect', 'hostname')
            if query == "None":
                html += '<h3>Please Select An Agency</h>'
                return
            sites = cswaDB.getSitesByOwner(config, form.get('agency'))
        except:
            raise

        for s in sites:
                writer.writerow((s[0], s[1], s[2], s[3]))

    else:
        try:
            rows = cswaDB.getloclist('range', form.get("lo.location1"), form.get("lo.location2"), 500, config)
        except:
            raise

        place = form.get("cp.place")
        if place != None and place != '':
            places = cswaGetAuthorityTree.getAuthority('places',  'Placeitem', place,  config.get('connect', 'connect_string'))
        else:
            places = []

        #rowcount = len(rows)

        for r in rows:
            objects = cswaDB.getlocations(r[0], '', 1, config, 'keyinfo', institution)
            #[sys.stderr.write('packing list csv objects: %s\n' % x[3]) for x in objects]
            for o in objects:
                if checkObject(places, o):
                    if institution == 'bampfa':
                        writer.writerow([o[x] for x in [0, 1, 3, 4, 6, 7, 9]])
                    else:
                        writer.writerow([o[x] for x in [0, 2, 3, 4, 5, 6, 7, 9]])

    return response



def doBarCodes(form, config):
    html = ''

    #updateactionlabel = config.get('info', 'updateactionlabel')
    updateType = config.get('info', 'updatetype')
    institution = config.get('info','institution')

    action = form.get('action')

    valid, error = validateParameters(form, config)
    if not valid: return html + error

    if action == "Create Labels for Locations Only":
        html += cswaConstants.getHeader('barcodeprintlocations',institution)
    else:
        html += cswaConstants.getHeader(updateType,institution)

    totalobjects = 0
    #If the group field has input, use that
    if form.get("gr.group") != '':
        sys.stderr.write('group: %s\n' % form.get("gr.group"))
        objs = cswaDB.getgrouplist(form.get("gr.group"), 5000, config)
        if action == 'Create Labels for Objects':
            totalobjects += len(objs)
            o = [o[0:8] + [o[9]] for o in objs]
            labelFilename = writeCommanderFile('objectrange', form.get("printer"), 'objectLabels', 'objects', o, config)
            html += '<tr><td>%s</td><td>%s</td><tr><td colspan="4"><i>%s</i></td></tr>' % (
                'objectrange', len(o), labelFilename)
    #If the museum number field has input, html += by object
    elif form.get('ob.objno1') != '':
        try:
            if form.get('ob.objno2'):
                objs = cswaDB.getobjlist('range', form.get("ob.objno1"), form.get("ob.objno2"), 1000, config)
            else:
                objs = cswaDB.getobjlist('range', form.get("ob.objno1"), form.get("ob.objno1"), 1000, config)
        except:
            raise
        if action == 'Create Labels for Objects':
            totalobjects += len(objs)
            o = [o[0:8] + [o[9]] for o in objs]
            labelFilename = writeCommanderFile('objectrange', form.get("printer"), 'objectLabels', 'objects', o, config)
            html += '<tr><td>%s</td><td>%s</td><tr><td colspan="4"><i>%s</i></td></tr>' % (
                'objectrange', len(o), labelFilename)
    else:
        try:
            #If no end location, assume single location
            if form.get("lo.location2"):
                rows = cswaDB.getloclist('range', form.get("lo.location1"), form.get("lo.location2"), 500, config)
            else:
                rows = cswaDB.getloclist('range', form.get("lo.location1"), form.get("lo.location1"), 500, config)
        except:
            raise

        rowcount = len(rows)

        objectsHandled = []
        rows.reverse()
        if action == "Create Labels for Locations Only":
            labelFilename = writeCommanderFile('locations', form.get("printer"), 'locationLabels', 'locations', rows, config)
            html += '<tr><td>%s</td><td colspan="4"><i>%s</i></td></tr>' % (len(rows), labelFilename)
            html += "\n</table>"
            return
        else:
            for r in rows:
                objects = cswaDB.getlocations(r[0], '', 1, config, updateType,institution)
                for o in objects:
                    if o[3] + o[4] in objectsHandled:
                        objects.remove(o)
                        html += '<tr><td>already printed a label for</td><td>%s</td><td>%s</td><td/></tr>' % (o[3], o[4])
                    else:
                        objectsHandled.append(o[3] + o[4])
                totalobjects += len(objects)
                # hack: move the ethnographic file code to the right spot for this app... :-(
                objects = [o[0:8] + [o[9]] for o in objects]
                labelFilename = writeCommanderFile(r[0], form.get("printer"), 'objectLabels', 'objects', objects, config)
                html += '<tr><td>%s</td><td>%s</td><tr><td colspan="4"><i>%s</i></td></tr>' % (
                    r[0], len(objects), labelFilename)

    html += """<tr><td align="center" colspan="4"><td></tr>"""
    html += """<tr><td align="center" colspan="4">"""
    if totalobjects != 0:
        if form.get('ob.objno1') or form.get('gr.group'):
            html += "<b>%s object barcode(s) printed." % totalobjects
        else:
            html += "<b>%s object(s)</b> found in %s locations." % (totalobjects, rowcount)
    else:
        html += '<span class="save">No objects found in this range.</span>'

    html += "\n</td></tr></table>"

    return html


def doAdvancedSearch(form, config):
    html = ''

    updateactionlabel = config.get('info', 'updateactionlabel')
    updateType = config.get('info', 'updatetype')
    institution = config.get('info','institution')
    groupby = form.get('groupby')

    valid, error = validateParameters(form, config)
    if not valid: return html + error

    dead,rare,qualifier = setFilters(form)

    beds = [form.get(i) for i in form if 'locations.' in i]
    taxa = [form.get(i) for i in form if 'taxon.' in i]
    places = [form.get(i) for i in form if 'places.' in i]

    #taxa: column = 1
    #family: column = 2
    #beds: column = 3
    #place: column = 5

    try:
        objects = cswaDB.getplants('', '', 1, config, 'getalltaxa', qualifier)
    except:
        raise

    html += cswaConstants.getHeader(updateType,institution)
    #totalobjects = 0
    accessions = []
    for t in objects:
        if checkMembership(t[1], taxa) and checkMembership(t[3], beds) and checkMembership(t[5],
            places) and checkMembership(t[7], rare) and checkMembership(t[8], dead):
            html += formatRow({'rowtype': updateType, 'data': t}, form, config)

    html += """</table><table>"""
    html += """<tr><td align="center">&nbsp;</tr>"""
    html += """<tr><td align="center"></tr>"""
    html += """<tr><td align="center">Report completed. %s objects displayed</td></tr>""" % (len(accessions))
    html += "\n</table>"

    return html


def doBedList(form, config):
    html = ''

    updateactionlabel = config.get('info', 'updateactionlabel')
    updateType = config.get('info', 'updatetype')
    institution = config.get('info','institution')
    groupby = form.get('groupby')

    valid, error = validateParameters(form, config)
    if not valid: return html + error

    dead,rare,qualifier = setFilters(form)

    if updateType == 'bedlist':
        rows = [form.get(i) for i in form if 'locations.' in i]
    # currently, the location report does not call this function. but it might...
    elif updateType == 'locreport':
        rows = [form.get(i) for i in form if 'taxon.' in i]

    rowcount = len(rows)
    totalobjects = 0
    if groupby == 'none':
        html += cswaConstants.getHeader(updateType + groupby, institution)
    else:
        html += '<table>'
    rows.sort()
    for headerid, l in enumerate(rows):

        try:
            objects = cswaDB.getplants(l, '', 1, config, updateType, qualifier)
        except:
            raise

        sys.stderr.write('%-13s:: %s\n' % (updateType, 'l=%s, q=%s, objects: %s' % (l,qualifier,len(objects))))
        if groupby == 'none':
            pass
        else:
            if len(objects) == 0:
                #html += '<tr><td colspan="6">No objects found at this location.</td></tr>'
                pass
            else:
                html += formatRow({'rowtype': 'subheader', 'data': [l, ]}, form, config)
                html += '<tr><td colspan="6">'
                html += cswaConstants.getHeader(updateType + groupby if groupby == 'none' else updateType, institution) % headerid

        for r in objects:
            #html += "<tr><td>%s<td>%s</tr>" % (len(places),r[6])
            # skip if the accession is not really in this location...
            #html += "<tr><td>loc = %s<td>this = %s</tr>" % (l,r[0])
            #if r[4] == '59.1168':
            #    html += "<tr><td>"
            #    html += r
            #    html += "</td></tr>"
            if (checkMembership(r[8],rare) and checkMembership(r[9],dead)) or r[12] == 'Dead':
                # nb: for bedlist, the gardenlocation (r[0]) is not displayed, so the next
                # few lines do not alter the display.
                if checkMembership(r[9],['dead']):
                    r[0] = "%s [%s]" % (r[10],r[12])
                r[0] = "%s = %s :: %s [%s]" % (r[9],r[0],r[10],r[12])
                totalobjects += 1
                html += formatRow({'rowtype': updateType, 'data': r}, form, config)

        if groupby == 'none':
            pass
        else:
            if len(objects) == 0:
                pass
            else:
                html += '</tbody></table></td></tr>'
                #html += """<tr><td align="center" colspan="6">&nbsp;</tr>"""

    if groupby == 'none':
        html += "\n</tbody></table>"
    else:
        html += '</table>'
    html += """<table><tr><td align="center"></tr>"""
    html += """<tr><td align="center">Bed List completed. %s objects, %s locations</td></tr>""" % (
        totalobjects, len(rows))
    html += "\n</table>"

    return html


def doHierarchyView(form, config):
    html = ''

    query = form.get('authority')
    if query == 'None':
        #hook
        html += '<h3>Please select an authority!</h3>'
        return
    res = cswaDB.gethierarchy(query, config)
    html += '<div id="tree">'
    #html += '<div id="tree"><table>'
    lookup = {concept.PARENT: concept.PARENT}
    link = ''
    hostname = config.get('connect', 'hostname')
    institution = config.get('info','institution')
    port = ''
    protocol = 'https'
    if query == 'taxonomy':
        link = protocol + '://' + hostname + port + '/collectionspace/ui/' + institution + '/html/taxon.html?csid=%s'
    elif query == 'places':
        link = protocol + '://' + hostname + port + '/collectionspace/ui/' + institution + '/html/place.html?csid=%s'
    else:
        link = protocol + '://' + hostname + port + '/collectionspace/ui/' + institution + '/html/concept.html?csid=%s&vocab=' + query
    for row in res:
        prettyName = row[0].replace('"', "'")
        if len(prettyName) > 0 and prettyName[0] == '@':
            #prettyName = '<' + prettyName[1:] + '> '
            prettyName = '<b>&lt;' + prettyName[1:] + '&gt;</b> '
        prettyName = '<a target="term" href="%s">%s</a>' % (link % (row[2]), prettyName)
        lookup[row[2]] = prettyName
    # html += '''var data = ['''
    #html += concept.buildJSON(concept.buildConceptDict(res), 0, lookup)
    # res = concept.buildJSON(concept.buildConceptDict(res), 0, lookup)
    html += concept.buildHTML(concept.buildConceptDict(res), 0, lookup)
    #x = ''
    #html += concept.printDict(concept.buildConceptDict(res), 0, lookup, x)
    #html += re.sub(r'\n    { label: "(.*?)"},', r'''\n    { label: "no parent >> \1"},''', res)
    #html += '</table></div>'
    html += '</div>'
#     html += """$(function() {
#     $('#tree').tree({
#         data: data,
#         autoOpen: true,
#         useContextMenu: false,
#         selectable: false
#     });
#     $('#tree').bind(
#     'tree.click',
#     function(event) {
#         // The clicked node is 'event.node'
#         var node = event.node;
#         var URL = node.url;
#         if (URL) {
#             window.open(URL);
#         }
#     }
# );
# });</script>"""
    #html += "\n</table>"
    html += "\n"

    return html


def doListGovHoldings(form, config):
    html = ''

    query = cswaDB.getDisplayName(config, form.get('agency'))
    if query is None:
        html += '<h3>Please Select An Agency: "%s" not found.</h>' % form.get('agency')
        return
    else:
        query = query[0]
    hostname = config.get('connect', 'hostname')
    institution = config.get('info', 'institution')
    protocol = 'https'
    port = ''
    link = protocol + '://' + hostname + port + '/collectionspace/ui/'+institution+'/html/place.html?csid='
    sites = cswaDB.getSitesByOwner(config, form.get('agency'))
    html += '<table width="100%">'
    html += '<tr><td class="subheader" colspan="4">%s</td></tr>' % query
    html += '''<tbody align="center" width=75 style="font-weight:bold">
        <tr><td>Site</td><td>Ownership Note</td><td>Place Note</td></tr></tbody>'''
    for site in sites:
        html += "<tr>"
        for field in site:
            if not field:
                field = ''
        html += '<td align="left"><a href="' + link + str(cswaDB.getCSID('placeName',site[0], config)[0]) + '&vocab=place">' + site[0] + '</td>'
        html += '<td align="left">' + (site[2] or '') + "</td>"
        html += '<td align="left">' + (site[3] or '') + "</td>"
        html += '</tr>'
    html += "</table>"
    html += '<h4> %s sites listed.</h4>' % len(sites)

    return html


def writeCommanderFile(location, printerDir, dataType, filenameinfo, data, config):
    # slugify the location
    slug = re.sub('[^\w-]+', '_', location).strip().lower()
    barcodeFile = config.get('files', 'cmdrfmtstring') % (
        dataType, printerDir, slug,
        datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S"), filenameinfo)

    newName = cswaSMBclient.uploadCmdrWatch(barcodeFile, dataType, data, config)

    return newName


def writeLog(updateItems, uri, httpAction, username, config):
    auditFile = config.get('files', 'auditfile')
    updateType = config.get('info', 'updatetype')
    myPid = str(os.getpid())
    # writing of individual log files is now disabled. audit file contains the same data.
    #logFile = config.get('files','logfileprefix') + '.' + datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S") + myPid + '.csv'

    # yes, it is inefficient open the log to write each row, but in the big picture, it's insignificant
    try:
        #csvlogfh = csv.writer(codecs.open(logFile,'a','utf-8'), delimiter="\t")
        #csvlogfh.writerow([updateItems['locationDate'],updateItems['objectNumber'],updateItems['objectStatus'],updateItems['subjectCsid'],updateItems['objectCsid'],updateItems['handlerRefName']])
        csvlogfh = csv.writer(codecs.open(auditFile, 'a', 'utf-8'), delimiter="\t")
        logrec = [ httpAction, datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"), updateType, uri, username ]
        for item in updateItems.keys():
            logrec.append("%s=%s" % (item, updateItems[item].replace('\n','#')))
        csvlogfh.writerow(logrec)
    except:
        raise
        #html += 'writing to log %s failed!' % auditFile
        pass


def writeInfo2log(request, form, config, elapsedtime):
    location1 = str(form.get("lo.location1"))
    action = str(form.get("action"))
    serverlabel = config.get('info', 'serverlabel')
    apptitle = config.get('info', 'apptitle')
    updateType = config.get('info', 'updatetype')
    institution = config.get('info', 'institution')
    checkServer = form.get('check')
    # override updateType if we are just checking the server
    if checkServer == 'check server':
        updateType = checkServer
    # sys.stderr.write('%-13s:: %-18s:: %-6s::%8.2f :: %-15s :: %s :: %s\n' % (updateType, action, request, elapsedtime, serverlabel))
    updateItems = {'app': apptitle, 'server': serverlabel, 'institution': institution, 'elapsedtime': '%8.2f' % elapsedtime, 'action': action}
    writeLog(updateItems, '', request, '', config)

def uploadFile(actualform, form, config):
    barcodedir = config.get('files', 'barcodedir')
    barcodeprefix = config.get('files', 'barcodeprefix')
    #html += form
    # we are using <form enctype="multipart/form-data"...>, so the file contents are now in the FieldStorage.
    # we just need to save it somewhere...
    fileitem = actualform['file']

    # Test if the file was uploaded
    if fileitem.filename:

        # strip leading path from file name to avoid directory traversal attacks
        fn = os.path.basename(fileitem.filename)
        # don't validate uploaded file (faster!)
        #success = processTricoderFile(fileitem, form, config)
        success = True
        if success:
            fileitem.file.seek(0,0)
            open(barcodedir + '/' + barcodeprefix + '.' + fn, 'wb').write(fileitem.file.read())
            os.chmod(barcodedir + '/' + barcodeprefix + '.' + fn, 0666)
            # for now, processing of Tricoder files by this webapp is disabled. john and julian 17 oct 2013
            #numUpdated = processTricoderFile(barcodedir + '/' + barcodeprefix + '.' + fn, form, config)
            message = '%s.%s was uploaded successfully to directory %s!' % (barcodeprefix,fn, barcodedir)
        else:
             message = 'Sorry, your file was rejected for errors.'
    else:
        message = 'No file was chosen to be uploaded. Please choose a file!'

    return "<h3>%s</h3>" % message


def doUploadUpdateLocs(data, line, id2ref, form, config):
    html = ''

    updateItems = {'crate': '', 'objectNumber': ''}
    if data[0] == "C":
        #Ex: "C","A1234567","07/22/2013 15:54","8-4216","Asian Archaeology Storage Box 0013","Kroeber, 20A, AA  1,  5"
        updateItems['handlerRefName'] = id2ref[data[1]]
        updateItems['locationDate'] = datetime.datetime.strptime(data[2], '%m/%d/%Y %H:%M').strftime("%Y-%m-%dT%H:%M:%SZ")
        updateItems['objectNumber'] = data[3]
        updateItems['crate'] = data[4]
        updateItems['locationRefname'] = cswaDB.getrefname('locations_common', data[5], config)
        updateItems['objectCsid'] = cswaDB.getCSID("objectnumber", data[3], config)[0]
        updateItems['reason'] = form.get('reason')
    elif data[0] == "M":
        #Ex: "M","A1234567","8-4216","Kroeber, 20A, AA  1,  1","07/22/2013 15:54"
        updateItems['handlerRefName'] = id2ref[data[1]]
        updateItems['objectNumber'] = data[2]
        updateItems['locationRefname'] = cswaDB.getrefname('locations_common', data[3], config)
        updateItems['objectCsid'] = cswaDB.getCSID("objectnumber", data[2], config)[0]
        updateItems['locationDate'] = datetime.datetime.strptime(data[4], '%m/%d/%Y %H:%M').strftime("%Y-%m-%dT%H:%M:%SZ")
        updateItems['reason'] = form.get('reason')
    elif data[0] == "R":
        #Ex: "R","A1234567","07/11/2013 17:29","Asian Archaeology Storage Box 0007","Kroeber, 20A, AA  1,  1"
        updateItems['handlerRefName'] = id2ref[data[1]]
        updateItems['locationDate'] = datetime.datetime.strptime(data[2], '%m/%d/%Y %H:%M').strftime("%Y-%m-%dT%H:%M:%SZ")
        updateItems['crate'] = data[3]
        #updateItems['locationRefname'], updateItems['objectCsid'] = cswaDB.getCSID('locations_common', data[4], config)
        updateItems['locationRefname'] = cswaDB.getrefname('locations_common', data[4], config)
        updateItems['objectCsid'] = cswaDB.getCSIDs('crateName', data[3], config)
        updateItems['reason'] = form.get('reason')
    else:
        raise Exception("<span style='color:red'>Error encountered in malformed line '%s':\nMove codes are M, C, or R!</span>" % line)

    updateItems[
        'subjectCsid'] = '' # cells[3] is actually the csid of the movement record for the current location; the updated value gets inserted later
    updateItems['inventoryNote'] = ''
    # if reason is a refname (e.g. bampfa), extract just the displayname
    reason = form.get('reason')
    reason = re.sub(r"^urn:.*'(.*)'", r'\1', reason)
    updateItems['computedSummary'] = updateItems['locationDate'][0:10] + (' (%s)' % reason)

    #html += updateItems
    numUpdated = 0
    try:
        if not isinstance(updateItems['objectCsid'], basestring):
            objectCsid = updateItems['objectCsid']
            for csid in objectCsid:
                updateItems['objectNumber'] = cswaDB.getCSIDDetail(config, csid[0], 'objNumber')
                updateItems['objectCsid'] = csid[0]
                updateLocations(updateItems, config)
                numUpdated += 1
                msg = 'Update successful'
                html += ('<tr>' + (3 * '<td class="ncell">%s</td>') + '</tr>\n') % (
                    updateItems['objectNumber'], updateItems['crate'], msg)
        else:
            updateLocations(updateItems, config)
            numUpdated += 1
            msg = 'Update successful'
            html += ('<tr>' + (3 * '<td class="ncell">%s</td>') + '</tr>\n') % (
                updateItems['objectNumber'], updateItems['inventoryNote'], msg)
    except:
        raise
        #raise Exception('<span style="color:red;">Problem updating line %s </span>' % line)
        #msg = 'Problem updating line %s' % line
        #html += ('<tr>' + (3 * '<td class="ncell">%s</td>') + '</tr>\n') % (
        #    updateItems['objectNumber'], updateItems['inventoryNote'], msg)
    return numUpdated,html


def updateKeyInfo(fieldset, updateItems, config, form):

    connection = cspace.connection.create_connection(MAINCONFIG, form['userdata'])

    message = ''

    uri = 'collectionobjects'
    getItems = updateItems['objectCsid']
    if getItems == None:
        url = "cspace-services/%s" % uri
    else:
        url = "cspace-services/%s/%s" % (uri, getItems)

    #Fields vary with fieldsets
    if fieldset == 'keyinfo':
        fieldList = ('pahmaFieldCollectionPlace', 'assocPeople', 'objectName', 'pahmaEthnographicFileCode')
    elif fieldset == 'namedesc':
        fieldList = ('briefDescription', 'objectName')
    elif fieldset == 'registration':
        # nb:  'pahmaAltNumType' is handled with  'pahmaAltNum'
        fieldList = ('objectName', 'pahmaAltNum', 'fieldCollector')
    elif fieldset == 'hsrinfo':
        fieldList = ('objectName', 'pahmaFieldCollectionPlace', 'briefDescription')
    elif fieldset == 'objtypecm':
        fieldList = ('objectName', 'collection', 'responsibleDepartment', 'pahmaFieldCollectionPlace')
    elif fieldset == 'collection':
        fieldList = ('objectName', 'collection')
    elif fieldset == 'placeanddate':
        fieldList = ('pahmaFieldLocVerbatim', 'pahmaFieldCollectionDate')


    # get the XML for this object getxml

    url, content, elapsedtime = connection.make_get_request(url)
    root = etree.fromstring(content)
    # add the user's changes to the XML
    for relationType in fieldList:
        #sys.stderr.write('tag1: %s\n' % relationType)
        # this app does not insert empty values into anything!
        if not relationType in updateItems.keys() or updateItems[relationType] == '':
            continue
        listSuffix = 'List'
        extra = ''
        if relationType in ['assocPeople', 'pahmaAltNum', 'pahmaFieldCollectionDate']:
            extra = 'Group'
        elif relationType in ['briefDescription', 'fieldCollector', 'responsibleDepartment']:
            listSuffix = 's'
        elif relationType in ['collection', 'pahmaFieldLocVerbatim']:
            listSuffix = ''
        else:
            pass
            #html += ">>> ",'.//'+relationType+extra+'List'
        #sys.stderr.write('tag2: %s\n' % (relationType + extra + listSuffix))
        metadata = root.findall('.//' + relationType + extra + listSuffix)
        try:
            metadata = metadata[0] # there had better be only one!
        except:
            # hmmm ... we didn't find this element in the record. Make a note a carry on!
            # message += 'No "' + relationType + extra + listSuffix + '" element found to update.'
            continue
        #print(etree.tostring(metadata))
        #html += ">>> ",relationType,':',updateItems[relationType]
        if relationType in ['assocPeople', 'objectName', 'pahmaAltNum']:
            #group = metadata.findall('.//'+relationType+'Group')
            #sys.stderr.write('  updateItem: ' + relationType + ':: ' + updateItems[relationType] + '\n' )
            Entries = metadata.findall('.//' + relationType)
            if not alreadyExists(updateItems[relationType], Entries):
                newElement = etree.Element(relationType + 'Group')
                leafElement = etree.Element(relationType)
                leafElement.text = updateItems[relationType]
                newElement.append(leafElement)
                if relationType in ['assocPeople', 'pahmaAltNum']:
                    apgType = etree.Element(relationType + 'Type')
                    apgType.text = updateItems[relationType + 'Type'].lower() if relationType == 'pahmaAltNum' else 'made by'
                    #sys.stderr.write(relationType + 'Type:' + updateItems[relationType + 'Type'])
                    newElement.append(apgType)
                if len(Entries) == 1 and Entries[0].text is None:
                    #sys.stderr.write('reusing empty element: %s\n' % Entries[0].tag)
                    #sys.stderr.write('ents : %s\n' % Entries[0].text)
                    #html += '<br>before',etree.tostring(metadata).replace('<','&lt;').replace('>','&gt;')
                    for child in metadata:
                        #html += '<br>tag: ', child.tag
                        if child.tag == relationType + 'Group':
                            #html += '<br> found it! ',child.tag
                            metadata.remove(child)
                    metadata.insert(0,newElement)
                    #html += '<br>after',etree.tostring(metadata).replace('<','&lt;').replace('>','&gt;')
                else:
                    metadata.insert(0,newElement)
            else:
                if IsAlreadyPreferred(updateItems[relationType], metadata.findall('.//' + relationType)):
                    continue
                else:
                    # exists, but not preferred. make it the preferred: remove it from where it is, insert it as 1st
                    for child in metadata:
                        if child.tag == relationType + 'Group':
                            checkval = child.find('.//' + relationType)
                            if checkval.text == updateItems[relationType]:
                                savechild = child
                                metadata.remove(child)
                    metadata.insert(0,savechild)
                pass
            # for AltNums, we need to update the AltNumType even if the AltNum hasn't changed
            if relationType == 'pahmaAltNum':
                apgType = metadata.find('.//' + relationType + 'Type')
                apgType.text = updateItems[relationType + 'Type']
                #sys.stderr.write('  updated: pahmaAltNumType to' + updateItems[relationType + 'Type'] + '\n' )
        elif relationType in ['briefDescription', 'fieldCollector', 'responsibleDepartment']:
            Entries = metadata.findall('.//' + relationType)
            #for e in Entries:
                #html += '%s, %s<br>' % (e.tag, e.text)
                #sys.stderr.write(' e: %s\n' % e.text)
            if alreadyExists(updateItems[relationType], Entries):
                if IsAlreadyPreferred(updateItems[relationType], Entries):
                    # message += "%s exists as %s, already preferred;" % (updateItems[relationType],relationType)
                    pass
                else:
                    # exists, but not preferred. make it the preferred: remove it from where it is, insert it as 1st
                    for child in Entries:
                        sys.stderr.write(' c: %s\n' % child.tag)
                        if child.text == updateItems[relationType]:
                            new_element = child
                            metadata.remove(child)
                            # message += '%s removed. len = %s<br/>' % (child.text, len(Entries))
                    metadata.insert(0,new_element)
                    message += " %s exists in %s, now preferred.<br/>" % (updateItems[relationType],relationType)
                    #html += 'already exists: %s<br>' % updateItems[relationType]
            # check if the existing element is empty; if so, use it, don't add a new element
            else:
                if len(Entries) == 1 and Entries[0].text is None:
                    #message += "removed %s ;<br/>" % (Entries[0].tag)
                    metadata.remove(Entries[0])
                new_element = etree.Element(relationType)
                new_element.text = updateItems[relationType]
                metadata.insert(0,new_element)
                message += "added preferred term %s as %s.<br/>" % (updateItems[relationType],relationType)

        elif relationType in ['pahmaFieldCollectionDate']:
            # we'll be replacing the entire structured date group
            pahmaFieldCollectionDateGroup = metadata.find('.//pahmaFieldCollectionDateGroup')
            newpahmaFieldCollectionDateGroup = etree.Element('pahmaFieldCollectionDateGroup')
            new_element = etree.Element('dateDisplayDate')
            new_element.text = updateItems[relationType]
            newpahmaFieldCollectionDateGroup.insert(0,new_element)
            if pahmaFieldCollectionDateGroup is not None:
                metadata.remove(pahmaFieldCollectionDateGroup)
            metadata.insert(0,newpahmaFieldCollectionDateGroup)

        else:
            # check if value is already present. if so, skip
            if alreadyExists(updateItems[relationType], metadata.findall('.//' + relationType)):
                if IsAlreadyPreferred(updateItems[relationType], metadata.findall('.//' + relationType)):
                    continue
                else:
                    message += "%s: %s already exists. Now duplicated with this as preferred.<br/>" % (relationType,updateItems[relationType])
                    pass
            newElement = etree.Element(relationType)
            newElement.text = updateItems[relationType]
            metadata.insert(0, newElement)
            #print(etree.tostring(metadata, pretty_print=True))
    objectCount = root.find('.//numberOfObjects')
    if 'objectCount' in updateItems:
        if objectCount is None:
            objectCount = etree.Element('numberOfObjects')
            collectionobjects_common = root.find(
                './/{http://collectionspace.org/services/collectionobject}collectionobjects_common')
            collectionobjects_common.insert(0, objectCount)
        objectCount.text = updateItems['objectCount']

    inventoryCount = root.find('.//inventoryCount')
    if 'inventoryCount' in updateItems:
        if inventoryCount is None:
            inventoryCount = etree.Element('inventoryCount')
            collectionobjects_pahma = root.find(
                './/{http://collectionspace.org/services/collectionobject/local/pahma}collectionobjects_pahma')
            collectionobjects_pahma.insert(0, inventoryCount)
        inventoryCount.text = updateItems['inventoryCount']
    #print(etree.tostring(root, pretty_print=True))

    if 'pahmaFieldLocVerbatim' in updateItems:
        pahmaFieldLocVerbatim = root.find('.//pahmaFieldLocVerbatim')
        if pahmaFieldLocVerbatim is None:
            pahmaFieldLocVerbatim = etree.Element('pahmaFieldLocVerbatim')
            pahmaFieldLocVerbatimobjects_common = root.find(
                './/{http://collectionspace.org/services/collectionobject/local/pahma}collectionobjects_pahma')
            pahmaFieldLocVerbatimobjects_common.insert(0, pahmaFieldLocVerbatim)
            message += " %s added as &lt;%s&gt;.<br/>" % (updateItems['pahmaFieldLocVerbatim'], 'pahmaFieldLocVerbatim')
        pahmaFieldLocVerbatim.text = updateItems['pahmaFieldLocVerbatim']

    collection = root.find('.//collection')
    if 'collection' in updateItems:
        if collection is None:
            collection = etree.Element('collection')
            collectionobjects_common = root.find(
                './/{http://collectionspace.org/services/collectionobject}collectionobjects_common')
            collectionobjects_common.insert(0, collection)
            message += " %s added as &lt;%s&gt;.<br/>" % (updateItems['collection'], 'collection')
        collection.text = updateItems['collection']



    uri = 'collectionobjects' + '/' + updateItems['objectCsid']
    payload = '<?xml version="1.0" encoding="UTF-8"?>\n' + etree.tostring(root,encoding='utf-8')
    # update collectionobject..
    #html += "<br>pretending to post update to %s to REST API..." % updateItems['objectCsid']
    elapsedtimetotal = time.time()
    messages = []
    messages.append("posting to %s REST API..." % uri)
    #print payload
    # messages.append(payload)
    (url, data, csid, elapsedtime) = postxml('PUT', uri, payload, form)

    return message

    #html += "<h3>Done w update!</h3>"


def createObject(objectinfo, config, form):

    message = ''

    uri = 'collectionobjects'

    # get the XML for this object
    content = '''<document name="collectionobjects">
<ns2:collectionobjects_common xmlns:ns2="http://collectionspace.org/services/collectionobject" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
<objectNameList>
<objectNameGroup>
<objectName/>
</objectNameGroup>
</objectNameList>
<objectNumber/>
</ns2:collectionobjects_common>
</document>'''

    x = '''
<ns2:collectionobjects_omca xmlns:ns2="http://collectionspace.org/services/collectionobject/local/omca" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
<sortableObjectNumber/>
</ns2:collectionobjects_omca>
'''

    root = etree.fromstring(content)
    for elementname in objectinfo:
        if elementname in objectinfo:
            element = root.find('.//' + elementname)
            element.text = objectinfo[elementname]

    uri = 'collectionobjects'
    payload = '<?xml version="1.0" encoding="UTF-8"?>\n' + etree.tostring(root,encoding='utf-8')
    # update collectionobject..
    sys.stderr.write("post new object %s to REST API..." % objectinfo['objectNumber'])
    #sys.stderr.write(etree.tostring(root))
    (url, data, csid, elapsedtime) = postxml('POST', uri, payload, form)
    sys.stderr.write("created new object with csid %s to REST API..." % csid)
    writeLog(objectinfo, uri, 'POST', '', config)
    # message = 'succeeded'

    return message, csid

    #html += "<h3>Done w update!</h3>"


def updateLocations(updateItems, config, form):
    institution = config.get('info', 'institution')

    uri = 'movements'

    #html += "<br>posting to movements REST API..."
    payload = lmiPayload(updateItems, institution)
    (url, data, csid, elapsedtime) = postxml('POST', uri, payload, form)
    updateItems['subjectCsid'] = csid

    uri = 'relations'

    #html += "<br>posting inv2obj to relations REST API..."
    updateItems['subjectDocumentType'] = 'Movement'
    updateItems['objectDocumentType'] = 'CollectionObject'
    payload = relationsPayload(updateItems)
    (url, data, csid, elapsedtime) = postxml('POST', uri, payload, form)

    # reverse the roles
    #html += "<br>posting obj2inv to relations REST API..."
    temp = updateItems['objectCsid']
    updateItems['objectCsid'] = updateItems['subjectCsid']
    updateItems['subjectCsid'] = temp
    updateItems['subjectDocumentType'] = 'CollectionObject'
    updateItems['objectDocumentType'] = 'Movement'
    payload = relationsPayload(updateItems)
    (url, data, csid, elapsedtime) = postxml('POST', uri, payload, form)

    writeLog(updateItems, uri, 'POST', '', config)

    #html += "<h3>Done w update!</h3>"


def formatRow(result, form, config):
    hostname = config.get('connect', 'hostname')
    institution = config.get('info', 'institution')
    port = ''
    protocol = 'https'
    rr = result['data']
    rr = [x if x != None else '' for x in rr]

    if result['rowtype'] == 'subheader':
        #return """<tr><td colspan="4" class="subheader">%s</td><td>%s</td></tr>""" % result['data'][0:1]
        return """<tr><td colspan="7" class="subheader">%s</td></tr>""" % result['data'][0]
    elif result['rowtype'] == 'location':
        return '''<tr><td class="objno"><a href="#" onclick="formSubmit('%s')">%s</a> <span style="color:red;">%s</span></td><td/></tr>''' % (
            result['data'][0], result['data'][0], '')
            #result['data'][0], result['data'][0], result['data'][-1])
    elif result['rowtype'] == 'select':
        rr = result['data']
        boxType = result['boxtype']
        return '''<li class="xspan"><input type="checkbox" name="%s.%s" value="%s" checked> <a href="#" onclick="formSubmit('%s')">%s</a></li>''' % (
            (boxType,) + (rr[0],) * 4)
        #return '''<tr><td class="xspan"><input type="checkbox" name="%s.%s" value="%s" checked> <a href="#" onclick="formSubmit('%s')">%s</a></td><td/></tr>''' % ((boxType,) + (rr[0],) * 4)
    elif result['rowtype'] == 'bedlist':
        groupby = str(form.get("groupby"))
        rare = 'Yes' if rr[8] == 'true' else 'No'
        dead = 'Yes' if rr[9] == 'true' else 'No'
        link = protocol + '://' + hostname + port + '/collectionspace/ui/'+institution+'/html/cataloging.html?csid=%s' % rr[7]
        if groupby == 'none':
            location = '<td class="zcell">%s</td>' % rr[0]
        else:
            location = ''
            # 3 recordstatus | 4 Accession number | 5 Determination | 6 Family | 7 object csid | 8 rare | 9 dead
        return '''<tr><td class="objno"><a target="cspace" href="%s">%s</a</td><td class="zcell">%s</td><td class="zcell">%s</td><td class="zcell">%s</td><td class="zcell">%s</td>%s</tr>''' % (
            link, rr[4], rr[6], rr[5], rare, dead,location)
    elif result['rowtype'] in ['locreport','holdings','advsearch']:
        rare = 'Yes' if rr[7] == 'true' else 'No'
        dead = 'Yes' if rr[8] == 'true' else 'No'
        link = protocol + '://' + hostname + port + '/collectionspace/ui/'+institution+'/html/cataloging.html?csid=%s' % rr[6]
        #  0 objectnumber, 1 determination, 2 family, 3 gardenlocation, 4 dataQuality, 5 locality, 6 csid, 7 rare , 8 dead , 9 determination (no author)
        return '''<tr><td class="zcell"><a target="cspace" href="%s">%s</a></td><td class="zcell">%s</td><td class="zcell">%s</td><td class="zcell">%s</td><td class="zcell">%s</td><td class="zcell">%s</td><td class="zcell">%s</td></tr>''' % (
            link, rr[0], rr[1], rr[2], rr[3], rr[5], rare, dead)
    elif result['rowtype'] == 'was.advsearch':
        link = protocol + '://' + hostname + port + '/collectionspace/ui/'+institution+'/html/cataloging.html?csid=%s' % rr[7]
        # 3 recordstatus | 4 Accession number | 5 Determination | 6 Family | 7 object csid
        #### 3 Accession number | 4 Data quality | 5 Taxonomic name | 6 Family | 7 object csid
        return '''<tr><td class="objno"><a target="cspace" href="%s">%s</a</td><td class="zcell">%s</td><td class="zcell">%s</td><td class="zcell">%s</td></tr>''' % (
            link, rr[4], rr[3], rr[5], rr[6])
    elif result['rowtype'] == 'inventory':
        link = protocol + '://' + hostname + port + '/collectionspace/ui/'+institution+'/html/cataloging.html?csid=%s' % rr[8]
        # loc 0 | lockey 1 | locdate 2 | objnumber 3 | objcount 4 | objname 5| movecsid 6 | locrefname 7 | objcsid 8 | objrefname 9
        # f/nf | objcsid | locrefname | [loccsid] | objnum
        if institution == 'bampfa':
            return """<tr><td class="objno"><a target="cspace" href="%s">%s</a></td><td class="objname">%s</td><td>%s</td><td class="rdo" ><input type="radio" id="sel-move" name="r.%s" value="found|%s|%s|%s|%s|%s" checked></td><td class="rdo" ><input type="radio" id="sel-nomove" name="r.%s" value="not found|%s|%s|%s|%s|%s"/></td><td class="zcell"><input class="xspan" type="text" size="65" name="n.%s"></td></tr>""" % (
            link, rr[3], rr[5], rr[16], rr[3], rr[8], rr[7], rr[6], rr[3], rr[14], rr[3], rr[8], rr[7], rr[6], rr[3], rr[14],
            rr[3])
        else:
            return """<tr><td class="objno"><a target="cspace" href="%s">%s</a></td><td class="objname">%s</td><td class="rdo" ><input type="radio" id="sel-move" name="r.%s" value="found|%s|%s|%s|%s|%s" checked></td><td class="rdo" ><input type="radio" id="sel-nomove" name="r.%s" value="not found|%s|%s|%s|%s|%s"/></td><td class="zcell"><input class="xspan" type="text" size="65" name="n.%s"></td></tr>""" % (
            link, rr[3], rr[5], rr[3], rr[8], rr[7], rr[6], rr[3], rr[14], rr[3], rr[8], rr[7], rr[6], rr[3], rr[14],
            rr[3])
    elif result['rowtype'] == 'powermove':
        link = protocol + '://' + hostname + port + '/collectionspace/ui/'+institution+'/html/cataloging.html?csid=%s' % rr[8]
        # loc 0 | lockey 1 | locdate 2 | objnumber 3 | objcount 4 | objname 5| movecsid 6 | locrefname 7 | objcsid 8 | objrefname 9
        # f/nf | objcsid | locrefname | [loccsid] | objnum
        if institution == 'bampfa':
            return """<tr><td class="objno"><a target="cspace" href="%s">%s</a></td><td class="objname">%s</td><td>%s</td><td class="rdo" ><input type="radio" id="sel-move" name="r.%s" value="found|%s|%s|%s|%s|%s"></td><td class="rdo" ><input type="radio" id="sel-nomove" name="r.%s" value="do not move|%s|%s|%s|%s|%s" checked/></td><td class="zcell"><input class="xspan" type="text" size="65" name="n.%s"></td></tr>""" % (
            link, rr[3], rr[5], rr[16], rr[3], rr[8], rr[7], rr[6], rr[3], rr[14], rr[3], rr[8], rr[7], rr[6], rr[3], rr[14],
            rr[3])
        return """<tr><td class="objno"><a target="cspace" href="%s">%s</a></td><td class="objname">%s</td><td class="rdo" ><input type="radio" id="sel-move" name="r.%s" value="move|%s|%s|%s|%s|%s"></td><td class="rdo" ><input type="radio" id="sel-nomove" name="r.%s" value="do not move|%s|%s|%s|%s|%s" checked/></td><td class="zcell"><input class="xspan" type="text" size="65" name="n.%s"></td></tr>""" % (
            link, rr[3], rr[5], rr[3], rr[8], rr[7], rr[6], rr[3], rr[14], rr[3], rr[8], rr[7], rr[6], rr[3], rr[14],
            rr[3])
    elif result['rowtype'] == 'moveobject':
        link = protocol + '://' + hostname + port + '/collectionspace/ui/'+institution+'/html/cataloging.html?csid=%s' % rr[8]
        # 0 storageLocation | 1 lockey | 2 locdate | 3 objectnumber | 4 objectName | 5 objectCount | 6 fieldcollectionplace | 7 culturalgroup |
        # 8 objectCsid | 9 ethnographicfilecode | 10 fcpRefName | 11 cgRefName | 12 efcRefName | 13 computedcraterefname | 14 computedcrate
        # f/nf | objcsid | locrefname | [loccsid] | objnum
        return """<tr><td class="rdo" ><input type="checkbox" name="r.%s" value="moved|%s|%s|%s|%s|%s" checked></td><td class="objno"><a target="cspace" href="%s">%s</a></td><td class="objname">%s</td><td class="zcell">%s</td><td class="zcell">%s</td></tr>""" % (
            rr[3], rr[8], rr[1], '', rr[3], rr[13], link, rr[3], rr[4], rr[5], rr[0])
    elif result['rowtype'] == 'keyinfo' or result['rowtype'] == 'objinfo':
        if institution == 'bampfa':
            link = protocol + '://' + hostname + port + '/collectionspace/ui/'+institution+'/html/cataloging.html?csid=%s' % rr[2]
            link2 = ''
        else:
            link = protocol + '://' + hostname + port + '/collectionspace/ui/'+institution+'/html/cataloging.html?csid=%s' % rr[8]
            link2 = protocol + '://' + hostname + port + '/collectionspace/ui/'+institution+'/html/acquisition.html?csid=%s' % rr[24]
        # loc 0 | lockey 1 | locdate 2 | objnumber 3 | objname 4 | objcount 5| fieldcollectionplace 6 | culturalgroup 7 | objcsid 8 | ethnographicfilecode 9
        # f/nf | objcsid | locrefname | [loccsid] | objnum
        return formatInfoReviewRow(form, link, rr, link2)
    elif result['rowtype'] == 'packinglist':
        if institution == 'bampfa':
            link = protocol + '://' + hostname + port + '/collectionspace/ui/'+institution+'/html/cataloging.html?csid=%s' % rr[2]
            return """
            <tr>
<td class="objno"><a target="cspace" href="%s">%s</a></td>
<td class="objname" name="ti.%s">%s</td>
<td class="ncell" name="ar.%s">%s</td>
<td class="ncell" name="me.%s">%s</td>
<td class="ncell" name="di.%s">%s</td>
<td class="ncell" name="cl.%s">%s</td>
</tr>""" % (link, rr[1], rr[2], rr[3], rr[2], rr[4], rr[2], rr[6], rr[2], rr[7], rr[2], rr[9])

        link = protocol + '://' + hostname + port + '/collectionspace/ui/'+institution+'/html/cataloging.html?csid=%s' % rr[8]
        # loc 0 | lockey 1 | locdate 2 | objnumber 3 | objname 4 | objcount 5| fieldcollectionplace 6 | culturalgroup 7 | objcsid 8 | ethnographicfilecode 9
        # f/nf | objcsid | locrefname | [loccsid] | objnum
        return """<tr>
<td class="objno"><a target="cspace" href="%s">%s</a></td>
<td class="objname" name="onm.%s">%s</td>
<td class="xspan" name="ocn.%s">%s</td>
<td class="xspan" name="cp.%s">%s</td>
<td class="xspan" name="cg.%s">%s</td>
<td class="xspan" name="fc.%s">%s</td>
</tr>""" % (link, rr[3], rr[8], rr[4], rr[8], rr[5], rr[8], rr[6], rr[8], rr[7], rr[8], rr[9])

    elif result['rowtype'] == 'packinglistbyculture':
        link = protocol + '://' + hostname + port + '/collectionspace/ui/'+institution+'/html/cataloging.html?csid=%s' % rr[8]
        # loc 0 | lockey 1 | locdate 2 | objnumber 3 | objname 4 | objcount 5| fieldcollectionplace 6 | culturalgroup 7x | objcsid 8 | ethnographicfilecode 9x
        # f/nf | objcsid | locrefname | [loccsid] | objnum
        return """<tr>
<td class="objno"><a target="cspace" href="%s">%s</a></td>
<td class="objname" name="onm.%s">%s</td>
<td class="xspan" name="ocn.%s">%s</td>
<td class="xspan">%s</td>
<td class="xspan" name="fc.%s">%s</td>
</tr>""" % (link, rr[3], rr[8], rr[4], rr[8], rr[5], rr[7], rr[8], rr[6])


def formatInfoReviewRow(form, link, rr, link2):
    """[0 Location, 1 Location Key, 2 Timestamp, 3 Museum Number, 4 Name, 5 Count, 6 Collection Place, 7 Culture, 8 csid,
        9 Ethnographic File Code, 10 Place Ref Name, 11 Culture Ref Name, 12 Ethnographic File Code Ref Name, 13 Crate Ref Name,
        14 Computed Crate 15 Description, 16 Collector, 17 Donor, 18 Alt Num, 19 Alt Num Type, 20 Collector Ref Name,
        21 Accession Number, 22 Donor Ref Name, 23 Acquisition ID, 24 Acquisition CSID]"""
    fieldSet = form.get("fieldset")
    if fieldSet == 'namedesc':
        return """<tr>
<td class="objno"><a target="cspace" href="%s">%s</a></td>
<td class="objname">
<input class="objname" type="text" name="onm.%s" value="%s">
</td>
<td width="0"></td>
<td class="zcell">
<input type="hidden" name="oox.%s" value="%s">
<input type="hidden" name="csid.%s" value="%s">
<textarea cols="78" rows="1" name="bdx.%s">%s</textarea></td>
</tr>""" % (link, cgi.escape(rr[3], True), rr[8], cgi.escape(rr[4], True), rr[8], cgi.escape(rr[3], True), rr[8], rr[8],
            rr[8], cgi.escape(rr[15], True))
    elif fieldSet == 'registration':
        altnumtypes, selected = cswaConstants.getAltNumTypes(form, rr[8], rr[19])
        return """<tr>
<td class="objno"><a target="cspace" href="%s">%s</a></td>
<td class="objname">
<input class="objname" type="text" name="onm.%s" value="%s">
</td>
<td class="zcell">
<input type="hidden" name="oox.%s" value="%s">
<input type="hidden" name="csid.%s" value="%s">
<input class="xspan" type="text" size="13" name="anm.%s" value="%s"></td>
<td class="zcell">%s</td>
<td class="zcell"><input class="xspan" type="text" size="26" name="pc.%s" value="%s"></td>
<td class="zcell"><span style="font-size:8">%s</span></td>
<td class="zcell"><a target="cspace" href="%s">%s</a></td>
</tr>""" % (link, cgi.escape(rr[3], True), rr[8], cgi.escape(rr[4], True), rr[8], cgi.escape(rr[3], True), rr[8], rr[8],
            rr[8], cgi.escape(rr[18], True), altnumtypes, rr[8], cgi.escape(rr[16], True),
            cgi.escape(rr[17], True), link2, cgi.escape(rr[21], True))
    elif fieldSet == 'keyinfo':
        return """<tr>
<td class="objno"><a target="cspace" href="%s">%s</a></td>
<td class="objname">
<input class="objname" type="text" name="onm.%s" value="%s">
</td>
<td class="veryshortinput">
<input class="veryshortinput" type="text" name="ocn.%s" value="%s">
</td>
<td class="zcell">
<input type="hidden" name="oox.%s" value="%s">
<input type="hidden" name="csid.%s" value="%s">
<input class="xspan" type="text" size="26" name="cp.%s" value="%s"></td>
<td class="zcell"><input class="xspan" type="text" size="26" name="cg.%s" value="%s"></td>
<td class="zcell"><input class="xspan" type="text" size="26" name="fc.%s" value="%s"></td>
</tr>""" % (link, cgi.escape(rr[3], True), rr[8], cgi.escape(rr[4], True), rr[8], rr[5], rr[8], cgi.escape(rr[3], True),
            rr[8], rr[8], rr[8], cgi.escape(rr[6], True), rr[8], cgi.escape(rr[7], True), rr[8], cgi.escape(rr[9], True))
    elif fieldSet == 'hsrinfo':
        return """<tr>
<td class="objno"><a target="cspace" href="%s">%s</a></td>
<td class="objname">
<input class="objname" type="text" name="onm.%s" value="%s">
</td>
<td class="veryshortinput">
<input class="veryshortinput" type="text" name="ocn.%s" value="%s">
</td>
<td class="zcell">
<input type="hidden" name="oox.%s" value="%s">
<input type="hidden" name="csid.%s" value="%s">
<input class="xspan" type="text" size="20" name="ctn.%s" value="%s"></td>
<td class="zcell"><input class="xspan" type="text" size="26" name="cp.%s" value="%s"></td>
<td class="zcell"><textarea cols="60" rows="1" name="bdx.%s">%s</textarea></td>
</tr>""" % (link, cgi.escape(rr[3], True), rr[8], cgi.escape(rr[4], True), rr[8], rr[5], rr[8], cgi.escape(rr[3], True),
            rr[8], rr[8], rr[8], cgi.escape(rr[25], True), rr[8], cgi.escape(rr[6], True), rr[8], cgi.escape(rr[15], True))
    elif fieldSet == 'objtypecm':
        objtypes, selected = cswaConstants.getObjType(form, rr[8], rr[26])
        collmans, selected = cswaConstants.getCollMan(form, rr[8], rr[27])
        return """<tr>
<td class="objno"><a target="cspace" href="%s">%s</a></td>
<td class="objname">
<input class="objname" type="text" name="onm.%s" value="%s">
</td>
<td class="veryshortinput">
<input class="veryshortinput" type="text" name="ocn.%s" value="%s">
</td>
<td>
<input type="hidden" name="oox.%s" value="%s">
<input type="hidden" name="csid.%s" value="%s">
%s</td>
<td>%s</td>
<td><input class="xspan" type="text" size="26" name="cp.%s" value="%s"></td>
<td><input type="checkbox"></td>
</tr>""" % (link, cgi.escape(rr[3], True), rr[8], cgi.escape(rr[4], True), rr[8], rr[5], rr[8], cgi.escape(rr[3], True),
                  rr[8], rr[8], objtypes, collmans, rr[8], cgi.escape(rr[6], True))
    elif fieldSet == 'collection':
                return """<tr>
<td class="objno"><a target="cspace" href="%s">%s</a></td>
<td class="objname">
<input type="hidden" name="onm.%s" value="">
%s
</td>
<input type="hidden" name="clnx.%s" value="%s">
<input type="hidden" name="csid.%s" value="%s">
<td><input class="xspan" type="text" size="40" name="cln.%s" value="%s"></td>
</tr>""" % (link, cgi.escape(rr[1], True), rr[2], cgi.escape(rr[3], True), rr[2], rr[22], rr[2], rr[2], rr[2], cgi.escape(rr[8], True))
    elif fieldSet == 'placeanddate':
                return """<tr>
<td class="objno"><a target="cspace" href="%s">%s</a></td>
<input type="hidden" name="csid.%s" value="%s">
<td class="objname"><input type="hidden" name="onm.%s" value="">%s</td>
<td><input class="xspan" type="text" size="40" name="vfcp.%s" value="%s"></td>
<td><input class="xspan" type="text" size="40" name="cd.%s" value="%s"></td>
</tr>""" % (link, cgi.escape(rr[3], True), rr[8], rr[8], rr[8], cgi.escape(rr[4], True), rr[8], cgi.escape(rr[28], True), rr[8], cgi.escape(rr[29], True))



def formatInfoReviewForm(form):
    fieldSet = form.get("fieldset")

    if fieldSet == 'namedesc':
        return """<tr><th>Object name</th><td class="objname"><input class="objname" type="text"  size="60" name="onm.user"></td>
</tr><tr><th>Brief Description</th><td class="zcell"><textarea cols="78" rows="7" name="bdx.user"></textarea></td>
</tr>"""
    elif fieldSet == 'registration':
        altnumtypes, selected = cswaConstants.getAltNumTypes(form, 'user','')
        return """<tr><th>Object name</th><td class="objname"><input class="objname" type="text"  size="60" name="onm.user"></td>
</tr><tr><th>Alternate Number</th><td class="zcell"><input class="xspan" type="text" size="60" name="anm.user"></td>
</tr><tr><th>Alternate Number Types</th><td class="zcell">%s</td>
</tr><tr><th>Field Collector (person)</th><td class="zcell"><input class="xspan" type="text" size="60" name="pc.user"></td>
</tr>""" % altnumtypes
    elif fieldSet == 'keyinfo':
        return """<tr><th>Object name</th><td class="objname"><input class="objname" type="text"  size="60" name="onm.user"></td>
</tr><tr><th>Count</th><td class="veryshortinput"><input class="veryshortinput" type="text" name="ocn.user"></td>
</tr><tr><th>Field Collection Place</th><td class="zcell"><input class="xspan" type="text" size="60" name="cp.user"></td>
</tr><tr><th>Cultural Group</th><td class="zcell"><input class="xspan" type="text" size="60" name="cg.user"></td>
</tr><tr><th>Ethnographic File Code</th><td class="zcell"><input class="xspan" type="text" size="60" name="fc.user"></td>
</tr>"""
    elif fieldSet == 'hsrinfo':
        return """<tr><th>Object name</th><td class="objname"><input class="objname" type="text" size="60" name="onm.user"></td>
</tr><tr><th>Count</th><td class="veryshortinput"><input class="veryshortinput" type="text" name="ocn.user"></td>
</tr><tr><th>Count Note</th><td class="zcell"><input class="xspan" type="text" size="25" name="ctn.user"></td>
</tr><tr><th>Field Collection Place</th><td class="zcell"><input class="xspan" type="text" size="50" name="cp.user"></td>
</tr><tr><th>Brief Description</th><td class="zcell"><textarea cols="60" rows="4" name="bdx.user"></textarea></td>
</tr>"""
    elif fieldSet == 'objtypecm':
        objtypes, selected = cswaConstants.getObjType(form, 'user', '')
        collmans, selected = cswaConstants.getCollMan(form, 'user', '')

        return """<tr><th>Object name</th><td class="objname"><input class="objname" type="text" size="60" name="onm.user"></td>
</tr><tr><th>Count</th><td class="veryshortinput"><input class="veryshortinput" type="text" name="ocn.user"></td>
</tr><tr><th>Object Type</th><td class="zcell">%s</td>
</tr><tr><th>Collection Manager</th><td class="zcell">%s</td>
</tr><tr><th>Field Collection Place</th><td><input class="xspan" type="text" size="60" name="cp.user"></td>
</tr>""" % (objtypes, collmans)
    elif fieldSet == 'collection':
        return """<tr><th>Object name</th><td class="objname"><input class="objname" type="text" size="60" name="onm.user"></td>
</tr><tr><th>Collection</th><td><input class="xspan" type="text" size="60" name="cn.user"></td>
</tr>"""
    elif fieldSet == 'placeanddate':
        return """<tr><th>Object name</th>
        <td class="objname"><input class="objname" type="text" size="60" name="onm.user"></td>
</tr>
<tr><th>FCP verbatim</th>
<td><input class="xspan" type="text" size="60" name="vfcp.user"></td>
</tr>"<tr><th>Collection Date</th>
<td><input class="xspan" type="text" size="60" name="cd.user"></td>
</tr>"""


def getxml(uri, realm, hostname, username, password, getItems):
    # port and protocol need to find their ways into the config files...
    port = ''
    protocol = 'https'
    server = protocol + "://" + hostname + port
    passman = urllib2.HTTPPasswordMgr()
    passman.add_password(realm, server, username, password)
    authhandler = urllib2.HTTPBasicAuthHandler(passman)
    opener = urllib2.build_opener(authhandler)
    urllib2.install_opener(opener)
    if getItems == None:
        url = "%s/cspace-services/%s" % (server, uri)
    else:
        url = "%s/cspace-services/%s/%s" % (server, uri, getItems)
    #sys.stderr.write('url %s' % url )
    elapsedtime = 0.0

    try:
        elapsedtime = time.time()
        f = urllib2.urlopen(url)
        data = f.read()
        elapsedtime = time.time() - elapsedtime
    except urllib2.HTTPError, e:
        sys.stderr.write('The server couldn\'t fulfill the request.')
        sys.stderr.write( 'Error code: %s' % e.code)
        raise
    except urllib2.URLError, e:
        sys.stderr.write('We failed to reach a server.')
        sys.stderr.write( 'Reason: %s' % e.reason)
        raise
    else:
        return (url, data, elapsedtime)

        #data = "\n<h3>%s :: %s</h3>" % e


def postxml(requestType, uri, payload, form):
    if WHEN2POST == 'now':
        connection = cspace.connection.create_connection(MAINCONFIG, form['userdata'])
        try:
            return connection.postxml(uri="cspace-services/"+uri, payload=payload, requesttype=requestType)
        except:
            raise
            return "%s REST API post failed..." % uri
        #return post2xml(requestType, uri, payload)
    else:
        return post2queue(requestType, uri, payload)


def post2queue(requestType, uri, payload):
    # relations records have dependencies -- these are handled by the queue consumer
    if uri != 'relations':
        element = json.dumps((requestType, uri, payload))
        DIRQ.add(element)
    return ('url', 'data', 'queued', 0.00)


def post2xml(requestType, uri, realm, hostname, username, password, payload):
    port = ''
    protocol = 'https'
    server = protocol + "://" + hostname + port
    passman = urllib2.HTTPPasswordMgr()
    passman.add_password(realm, server, username, password)
    authhandler = urllib2.HTTPBasicAuthHandler(passman)
    opener = urllib2.build_opener(authhandler)
    urllib2.install_opener(opener)
    url = "%s/cspace-services/%s" % (server, uri)
    elapsedtime = 0.0

    elapsedtime = time.time()
    request = urllib2.Request(url, payload, {'Content-Type': 'application/xml'})
    # default method for urllib2 with payload is POST
    if requestType == 'PUT': request.get_method = lambda: 'PUT'
    try:
        f = urllib2.urlopen(request)
    except urllib2.URLError, e:
        if hasattr(e, 'reason'):
            sys.stderr.write('We failed to reach a server.\n')
            sys.stderr.write('Reason: ' + str(e.reason) + '\n')
        if hasattr(e, 'code'):
            sys.stderr.write('The server couldn\'t fulfill the request.\n')
            sys.stderr.write('Error code: ' + str(e.code) + '\n')
        if True:
            #html += 'Error in POSTing!'
            sys.stderr.write("Error in POSTing!\n")
            sys.stderr.write(url)
            sys.stderr.write(payload)
            raise

    data = f.read()
    info = f.info()
    # if a POST, the Location element contains the new CSID
    if info.getheader('Location'):
        csid = re.search(uri + '/(.*)', info.getheader('Location'))
        csid = csid.group(1)
    else:
        csid = ''
    elapsedtime = time.time() - elapsedtime
    return (url, data, csid, elapsedtime)

