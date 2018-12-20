import ConfigParser

tenants = 'bampfa botgarden cinefiles pahma ucjeps'.split(' ')

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
        if not app in all_apps:
            all_apps[app]  = {}
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