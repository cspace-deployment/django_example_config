import ConfigParser
import sys

MUSEUMS = [
    ['UC Botanical Garden', 'botgarden', '13d90c7c-60cc-4f13-9985'],
    ['Berkeley Art Museum', 'bampfa', 'a558ed9e-e4cd-4680-87d3'],
    ['Pacific File Archive', 'cinefiles', '331dfe82-7877-4484-8f20'],
    ['PAHMA', 'pahma', 'c8055214-50e7-49b1-b15b'],
    ['UCJEPS', 'ucjeps', '1c18cf1e-4826-4f33-b047']
]

header = """
    <style>
    li {margin: 10px 0;}
    p.landing { padding: 2px; }
    p { padding: 2px; }
    td { text-align: center; max-height: 120px; }
    h3, h4 { padding: 0px; margin-bottom: 6px; margin-top: 6px; color: #4d4d4d; }
    </style>
"""

def wrap(tag, value):
    return '<%s>%s</%s>' % (tag, value, tag)


def app_anchor(link_text, tenant, app, deployment):
    return '<a href="https://webapps%s.cspace.berkeley.edu/%s/%s" target="webapp">%s</a>' % (deployment, tenant, app, link_text)


def app_image(app):
    return '<img src="https://webapps.cspace.berkeley.edu/%s.jpg" target="webapp">' % app


try:
    output_type = sys.argv[1]
except:
    output_type = 'text'

tenants = 'bampfa botgarden cinefiles pahma ucjeps'.split(' ')
dont_show = 'hello service suggest suggestsolr suggestpostgres'.split(' ')

config = ConfigParser.RawConfigParser()

all_apps = {}

for tenant in tenants:
    relative_path = tenant + '/config/landing.cfg'
    config.read(relative_path)
    hiddenApps = config.get('landing', 'hiddenApps').split(',')
    publicApps = config.get('landing', 'publicApps').split(',')
    apps = __import__(tenant + '.project_apps', fromlist=[''])
    appList = [app for app in apps.INSTALLED_APPS if not "django" in app]
    for app in appList:
        token = ''
        if app in dont_show and output_type != 'text': continue
        if not app in all_apps:
            all_apps[app] = {}
        if app in publicApps:
            token = 'Public'
        else:
            token = 'Private'
        if app in hiddenApps:
            # check if an app is marked Public but is listed as hidden
            if token == 'Public':
                token = 'Error!'
            token = 'Hidden'
        all_apps[app][tenant] = token

if output_type == 'text':

    print '%-20s' % 'apps',
    for tenant in tenants:
        print '%-15s' % tenant,
    print

    for app in sorted(all_apps.keys()):
        print '%-20s' % app,
        for tenant in tenants:
            if tenant in all_apps[app]:
                print '%-15s' % all_apps[app][tenant],
            else:
                print '%-15s' % ' ',
        print
else:
    print header
    print '<table style="cell-padding: 8px;" border="1">'
    # print '<tr><th>%s' % ''
    # for app in sorted(all_apps.keys()):
    #     print wrap('th',app)
    # print '</tr>'
    print '<tr><th>%s' % ''
    for app_type in 'Public Private'.split(' '):
        print wrap('th', app_type)
    print '</tr>'
    for tenant in tenants:
        print '<tr>', wrap('th', tenant)
        for app_type in 'Public Private'.split(' '):
            print '<td>'
            for app in sorted(all_apps.keys()):
                if tenant in all_apps[app]:
                    if all_apps[app][tenant] == app_type:
                        print wrap('div', app_anchor(app_image(app) + '<br/>' + app, tenant, app, ''))
                else:
                    pass
                    # print wrap('td',' ')
            print '</td>'
        print '</tr>'
    print '</table>'

if False:

    print '%-10s' % ' ',
    for app in sorted(all_apps.keys()):
        print '%-10s' % app,
    print
    for tenant in tenants:
        print '%-10s' % tenant,
        # print '%-20s' % app,
        for app in sorted(all_apps.keys()):
            if tenant in all_apps[app]:
                print '%-10s' % all_apps[app][tenant],
            else:
                print '%-10s' % ' ',
        print
