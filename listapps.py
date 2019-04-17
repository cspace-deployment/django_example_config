import ConfigParser
import sys

PAGE="""<html lang="en-us">
<head>
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
    <meta name="robots" content="NONE,NOARCHIVE">
    <link rel="stylesheet" href="//code.jquery.com/ui/1.11.4/themes/smoothness/jquery-ui.css"/>
    <script src="//code.jquery.com/jquery-1.10.2.js"></script>
    <script src="//code.jquery.com/ui/1.11.4/jquery-ui.js"></script>
    <!-- link rel="stylesheet" type="text/css" href="css/smoothness/jquery-ui-1.8.22.custom.css"/>
    <script type="text/javascript" src="js/jquery-1.10.0.min.js"></script>
    <script type="text/javascript" src="js/jquery-ui-1.10.3.custom.min.js"></script -->
    <link rel="stylesheet" type="text/css" href="css/base.css">
    <style>
    li {margin: 10px 0;}
    .likeabutton {
        appearance: button;
        -moz-appearance: button;
        -webkit-appearance: button;
        text-decoration: none; font: menu; color: ButtonText;
        display: inline-block;
    }
    p { margin: 2px; }
    h3, h4 { padding: 0px; margin-bottom: 6px; margin-top: 6px; color: #4d4d4d; }
    </style>
</head>
<body class="">
<div id="container">
    <div id="content-main" style="max-width: 1000px;">
        <div>
            <img height="40px" src="http://www.collectionspace.org/wp-content/uploads/2014/11/CSpaceLogo.png">
            <span style="font-size: 28px;vertical-align: 35%%;">@</span>
            <img height="60px" src="https://www.berkeley.edu/brand/berkeley-logo.png">
        </div>
         <div id="tabs">
            <ul>
                <li><a href="#prodtab">Production Apps</a></li>
                <li><a href="#devtab">Development Apps</a></li>
                <li><a href="#documentstab">Help!</a></li>
                <li><a href="#analyticstab">Analytics</a></li>
                <li><a href="#otheruserstab">Other Public Portals</a></li>
                <li><a href="#newstab">News</a></li>
            </ul>
            <div id="prodtab">
                <h3>Links to <span style="color: red">Production</span> Systems</h3>
                %s
            </div>

            <div id="devtab">
                <h3>Links to <span style="color: green">Development</span> Systems</h3>
                %s
            </div>
             <div id="analyticstab">
                 <div id="analyticspages">
                     <ul>
                         <li><a href="#djangotab">Django Webapp Usage</a></li>
                         <li><a href="#toolboxtab">Toolbox Webapp Usage</a></li>
                         <li><a href="#solrcoretab">Contents of Public Solr Cores</a></li>
                     </ul>
                     <div id="djangotab">
                         <iframe style="width: 100%%; height: 1000px;" src="summary.html"></iframe>
                     </div>
                     <div id="toolboxtab">
                         <iframe style="width: 100%%; height: 1000px;" src="webappuse.html"></iframe>
                     </div>
                     <div id="solrcoretab">
                         <iframe style="width: 100%%; height: 1000px;" src="corestats.html"></iframe>
                     </div>
                 </div>
             </div>
             <div id="documentstab">
                 <h3>Hello!</h3>
                 <p>There is no one single place to find information and links to the various services and websites
                 associated with CollectionSpace@UCB.  This is probably as close as you will get to such a place.</p>
                 <p>This webpage and its various panes provide links to web-accessible CSpace applications at UCB.</p>
                 <p>For each set of applications, are two "deployments" (i.e. installations) of the code:</p>
                 <ul>
                     <li>The <span style="color: red">Production</span> deployment, where "real work" should be done;</li>
                     <li>The <span style="color: green">Development</span>  deployment, where testing, experimentation, and training should be done.</li>
                 </ul>
                 The first two tabs (above left) show what is available for each deployment.</p>
                 <p>
                     <b>Make sure you are working with the deployment you should be working with!</b></b>
                 </p>
                 <p>There are two basic types of applications:</p>
                 <ul>
                 <li>Webapps written using the <a target="new" href="https://github.com/cspace-deployment/cspace_django_project/blob/master/README.md">CollectionSpace Django Project</a></li>
                 <li>The <a target="new" href="">"regular UIs"</a>, which require authentication.</li>
                </ul>
            </div>
             <div id="otheruserstab">
                 <h3>Other Public Portals</h3>
                 <p>The following is a list of other deployments of the Search Portal software that we know about.</p>
                 <p>Please let us know if you find others:</p>
                 <ul>
                     <li>Bolinas Museum <a target="_new" href="http://collection.bolinasmuseum.org/webapp/search">http://collection.bolinasmuseum.org/webapp/search</a></li>
                     <li>Watermill Center <a target="_new" href="http://collection.watermillcenter.org/search">http://collection.watermillcenter.org/search</a></li>
                 </ul>
            </div>
            <div id="newstab">
            </div>
        </div>
    </div>
    <br class="clear">
</div>
<!-- END Content -->
<div id="footer"></div>
<!-- END Container -->
<script>
        $('#tabs').tabs({active: 0});
        $('#analyticspages').tabs({active: 0});
</script>

<script>
  (function(i,s,o,g,r,a,m){i['GoogleAnalyticsObject']=r;i[r]=i[r]||function(){
  (i[r].q=i[r].q||[]).push(arguments)},i[r].l=1*new Date();a=s.createElement(o),
  m=s.getElementsByTagName(o)[0];a.async=1;a.src=g;m.parentNode.insertBefore(a,m)
  })(window,document,'script','https://www.google-analytics.com/analytics.js','ga');
  ga('create', 'UA-54952024-5', 'auto');
  ga('send', 'pageview');
</script>
</body>
</html>"""

MUSEUMS = {
    'botgarden': ['UC Botanical Garden', '13d90c7c-60cc-4f13-9985'],
    'bampfa': ['Berkeley Art Museum', 'a558ed9e-e4cd-4680-87d3'],
    'cinefiles': ['Pacific File Archive', '331dfe82-7877-4484-8f20'],
    'pahma': ['Phoebe A. Hearst Museum of Anthropology', 'c8055214-50e7-49b1-b15b'],
    'ucjeps': ['University and Jepson Herbaria', '1c18cf1e-4826-4f33-b047']
}

APPS = {
    'imagebrowser': 'Image Browser',
    'imaginator': 'Imaginator',
    'eloan': 'e-Loans',
    'cinestats': '"CineStats"',
    'csvimport': 'csvImport',
    'searchmedia': 'Media Search',
    'grouper': 'Grouper',
    'internal': 'Internal Portal',
    'search': 'Public Portal',
    'osteology': 'Osteology Portal',
    'publicsearch': '"legacy" Public Portal',
    'ireports': 'iReports',
    'uploadmedia': 'Bulk Media Upload',
    'uploadtricoder': 'Tricoder File Upload',
    'taxoneditor': 'Taxon Editor',
    'toolbox': 'Toolbox',
    'locationhistory': 'Location History',
    'workflow': 'Workflow Helper'

}

header = """
    <style>
    li {margin: 10px 0;}
    p.landing { padding: 2px; }
    p { padding: 2px; }
    td { text-align: center; max-height: 120px; }
    h3, h4 { padding: 0px; margin-bottom: 6px; margin-top: 6px; color: #4d4d4d; }
    </style>
"""

cell = """
<tr>
<td style="width: 340px; vertical-align: top;">
<a  class="likeabutton" target="_blank" href="https://%sDEPLOYMENT.cspace.berkeley.edu">
<h4>%s</h4>
<img style="max-width: 330px ; max-height: 100px" alt="%s" src="https://webapps.cspace.berkeley.edu/%s_static/cspace_django_site/images/header-logo.png"></a>
</td>
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
    html = '<table>'
    html += '<tr><th>%s' % ''
    for app_type in 'Public Private'.split(' '):
        html += wrap('td', wrap('b', app_type)).replace('<td>', '<td style="width: 300px;">')
    html += '</tr>'
    for tenant in tenants:
        html += cell % (tenant, MUSEUMS[tenant][0], MUSEUMS[tenant][0], tenant)
        for app_type in 'Public Private'.split(' '):
            html += '<td style="vertical-align: top; padding-top: 20px;">'
            for app in sorted(all_apps.keys()):
                if tenant in all_apps[app]:
                    if all_apps[app][tenant] == app_type:
                        app_name = APPS[app] if app in APPS else app
                        html += wrap('p', app_anchor(app_name, tenant, app, 'DEPLOYMENT'))
                else:
                    pass
                    # html += wrap('td',' ')
            html += '</td>'
        html += '</tr>'
    html += '</table>'

    print PAGE % (html.replace('DEPLOYMENT',''), html.replace('DEPLOYMENT','-dev'))

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
