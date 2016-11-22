import os
import csv
import ConfigParser

from common import cspace  # we use the config file reading function
from cspace_django_site import settings

import constants


def convert2int(s):
    try:
        return int(s)
    except ValueError:
        return s


def getapplist(myappdir, thisInstitution, thisDeployment):
    files = os.listdir(myappdir)
    badconfigfiles = []

    webapps = {'listapps': ['Available Tools', 'red', None, 'green']}

    for configfile in files:
        if '.cfg' in configfile:
            config = ConfigParser.RawConfigParser()
            config.read(os.path.join(myappdir, configfile))
            try:
                deployment = config.get('info', 'serverlabel')
                institution = config.get('info', 'institution')
                # only show options for this deployment and institution ignore other config files
                if deployment != thisDeployment or institution != thisInstitution:
                    continue
                logo = config.get('info', 'logo')
                updateType = config.get('info', 'updatetype')
                schemacolor1 = config.get('info', 'schemacolor1')
                institution = config.get('info', 'institution')
                apptitle = config.get('info', 'apptitle')
                serverlabelcolor = config.get('info', 'serverlabelcolor')
                webapps[updateType] = [apptitle, serverlabelcolor, configfile, schemacolor1, logo]
            except:
                badconfigfiles.append(configfile)

    if badconfigfiles != []:
        webapps['badconfigfiles'] = badconfigfiles

    return webapps


def getdropdown(dropdown):
    form = {'institution': institution}
    if dropdown == 'tricoderusers':
        return constants.tricoderUsers()
    elif dropdown == 'handlers':
        return constants.getHandlers(form)
    elif dropdown == 'reasons':
        return constants.getReasons(form)
    elif dropdown == 'printers':
        return constants.getPrinters(form)
    elif dropdown == 'fieldset':
        return constants.getFieldset(form)
    elif dropdown == 'hierarchies':
        return constants.getHierarchies(form)
    elif dropdown == 'altnumtypes':
        return constants.getAltNumTypes(form)
    elif dropdown == 'objtype':
        return constants.getObjType(form)
    elif dropdown == 'collman':
        return constants.getCollMan(form)
    elif dropdown == 'agencies':
        return constants.getAgencies(form)
    elif dropdown == 'activities':
        return constants.getActivities(form)
    elif dropdown == 'periods':
        return constants.getPeriods(form)

    return '', ''


def definefields(parmFile, suggestions):
    columns = "id app name label role type parameter autocomplete row column".split(" ")

    try:
        f = open(parmFile, 'rb')
        csvfile = csv.reader(f, delimiter="\t")
    except IOError:
        raise
        message = 'Expected to be able to read %s, but it was not found or unreadable' % parmFile
        return message, -1
    except:
        raise

    try:
        appLayout = {}
        for row in csvfile:
            if row[0] == '': continue
            if row[0][0] == '#': continue
            if row[1][0] == '#': continue
            app = row[1]
            role = row[4]
            if suggestions == 'postgres' and row[7] != '':
                row[2] = '%s.%s' % (row[7], row[2])
            if not app in appLayout:
                appLayout[app] = {}
            if not role in appLayout[app]:
                appLayout[app][role] = []
            # if not varname in appLayout[app][role]:
            #    appLayout[app][role][varname] = []
            pdict = {}
            for r, v in enumerate(columns):
                if columns[r] in "id name label type parameter row column".split(" "):
                    pdict[v] = convert2int(row[r])
            if pdict['type'] == 'dropdown':
                pdict['parameter'] = getdropdown(row[6])
            if pdict['type'] == 'button':
                del pdict['column']
                del pdict['row']
            appLayout[app][role].append(pdict)
            # if varname in 'start review enumerate move movecheck end'.split(' '):
            # pass
            # appLayout[app][role]['nextstate'] = row[6]

        f.close()

        return appLayout

    except IOError:
        message = 'Could not read (or maybe parse) rows from %s' % parmFile
        return message, -1
    except:
        raise


# global variables

config = cspace.getConfig(os.path.join(settings.BASE_PARENT_DIR, 'config'), 'toolbox')
APPDIR = os.path.join(settings.BASE_PARENT_DIR, 'toolbox', config.get('info', 'appdir'))
institution = config.get('info', 'institution')
deployment = config.get('info', 'serverlabel')
connect_string = config.get('connect', 'connect_string')
schemacolor1 = config.get('info', 'schemacolor1')
deploymentcolor = config.get('info', 'serverlabelcolor')
APPS = getapplist(APPDIR, institution, deployment)
APPS['json'] = ['JSON']
try:
    suggestions = config.get('connect', 'suggestions')
except:
    suggestions = None

appLayout = definefields(os.path.join(settings.BASE_PARENT_DIR, 'toolbox', APPDIR, 'layout.csv'), suggestions)

try:
    VERSION = os.popen("cd " + settings.BASE_PARENT_DIR + " ; /usr/bin/git describe --always").read().strip()
    if VERSION == '':  # try alternate location for git (this is the usual Mac location)
        VERSION = os.popen("/usr/local/bin/git describe --always").read().strip()
except:
    VERSION = 'Unknown'
