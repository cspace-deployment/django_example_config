import re
import django_tables2 as tables
from constants import getAgencies, getHierarchies
import dbqueries
from toolbox import activity2db


def select_cells(applayout, row):
    newrow = []
    return [row[i] for i in [3,4,5,6,7,8]]


def extractTerms(context, dict, requestedField):
    field = None
    position = None
    for fieldname in 'date location crate object authority taxon reason handler groupby culture concept activity'.split(' '):
        if '.start' in requestedField:
            position = 'start'
        if '.end' in requestedField:
            position = 'end'
        if fieldname in requestedField:
            field = fieldname
            break
    return [position, field, dict[requestedField], context['applayout'][requestedField]['label'], requestedField]


def getFields(request, context):
    search_terms = {}
    for formField in request.POST:
        if formField in 'csrfmiddlewaretoken submit start enumerate search update movecheck'.split(' '): continue
        if 'select-' in formField: continue  # skip select items that may be in form
        if 'item-' in formField: continue
        # if not requestObject[p]: continue # uh...looks like we can have empty items...let's skip 'em
        search_terms[formField] = extractTerms(context, request.POST, formField)
    return search_terms


def doDemoQuery(query, fields):
    # this just returns 40 rows of data from the portal...
    import demodata

    data = demodata.sampledata()
    rows = []
    for d in data:
        row = []
        for field in fields:
            if field in d:
                row.append(d[field])
            else:
                row.append('')
        cells = {'csid': d['csid_s'], 'cells': row}
        rows.append(cells)
    data = rows

    return data


def doQuery(request, context):
    appname = request['appname']

    #if not dbqueries.validateParameters(form, config): return

    table = []
    if appname in 'keyinfo packinglist inventory movecrate moveobject'.split(' '):
        try:
            locationList = dbqueries.getloclist('range', request["lo.location.start"], request["lo.location.end"], 500)
        except:
            raise

        totalobjects = 0
        totallocations = 0
        for location in locationList:

            try:
                objects = dbqueries.getlocations(location[0], '', 1, appname)
            except:
                raise

            chunk = {'subheader': location[0]}
            totallocations += 1
            items = []
            for r in objects:
                totalobjects += 1
                r = select_cells(context['applayout'], r)
                items.append({'csid': 'xxx', 'cells': r})
            chunk['items'] = items
            table.append(chunk)

    elif appname in 'objdetails objinfo'.split(' '):
        pass

    elif appname in 'grpinfo grpmove'.split(' '):
        pass

    return table


def doSearch(context, request):
    context['checkitems'] = getFields(request, context)
    return context


def getData(context,request):
    context ={}
    for formField in request.GET:
        context[formField] = request.GET[formField]

    # import datelist
    # print getitems('collectionobjects', 100, '1999-01-01', '2015-05-01', 'month')
    # data = datelist.datelist

    num2ret = context['num2ret']
    period = context['period']
    table = context['activity']
    start = context['start']
    end = context['end']
    data = activity2db.getitems(table, num2ret, start, end, period)

    context['data'] = data
    context['numberofitems'] = len(data)
    return context


def doActivity(context, request):
    context['checkitems'] = getFields(request, context)

    forminput = getFields(request, context)
    if 'items' in context: del context['items']
    context['action'] = 'enumerate'

    # import datelist
    # daterange = datelist.datelist
    # getitems(table, num2ret, start_date, end_date, period)
    # print getitems('collectionobjects', 100, '1999-01-01', '2015-05-01', 'month')

    num2ret = 500
    period = forminput['period'][2]
    table = forminput['activity'][2]
    start = forminput['date.start'][2]
    end = forminput['date.end'][2]

    context['num2ret'] = num2ret
    context['period'] = period
    context['activity'] = table
    context['start'] = start
    context['end'] = end
    daterange = activity2db.getitems(table, num2ret, start, end, period)

    rows = []
    for d in daterange:
        row = {}
        for i,field in enumerate('count date'.split(' ')):
            row[field] = d[i]
        rows.append(row)
    data = rows

    class NameTable(tables.Table):

        count = tables.Column(verbose_name='count')
        date = tables.Column(verbose_name='date')

    table = NameTable(data)

    context['reviewitems'] = table
    context['numberofitems'] = len(data)

    context['action'] = 'end'

    return context


def doEnumerate(context, request):
    data = doDemoQuery('query', 'objmusno_s objname_s objcount_s objfcpverbatim_s objfilecode_ss objassoccult_ss'.split(' '))

    context['items'] = data
    context['numberofitems'] = len(data)

    return context


def doReview(context, request):
    data = doQuery(request, context)

    context['table'] = data
    context['numberofitems'] = len(data)

    return context


def doUpdate(context, request):
    context['items'] = doDemoQuery('query', 'objmusno_s objname_s id'.split(' '))
    context['numberofitems'] = len(context['items'])

    return context


def doSave(context, request):
    context['checkitems'] = getFields(request, context)

    return context


def doMovecheck(context, request):
    context['checkitems'] = getFields(context, request)

    return context

def xxx(request,context,config):
    hierarchies = getHierarchies()
    context['hierarchies'] = hierarchies
    if "hierarchy" in request.GET:
        hierarchy = request.GET["hierarchy"]
        context['selected_hierarchy'] = hierarchy
        config_file_name = 'HierarchyViewer'
        res = dbqueries.gethierarchy(hierarchy, config)
        hostname = config.get('connect', 'hostname')
        institution = config.get('info', 'institution')
        port = config.get('link', 'port')
        protocol = config.get('link', 'protocol')
        link = protocol + '://' + hostname + port + '/collectionspace/ui/' + institution
        if hierarchy == 'taxonomy':
            link += '/html/taxon.html?csid=%s'
        elif hierarchy == 'places':
            link += '/html/place.html?csid=%s'
        else:
            link += '/html/concept.html?csid=%s&vocab=' + hierarchy
        for row in res:
            pretty_name = row[0].replace('"', "'")
            if len(pretty_name) > 0 and pretty_name[0] == '@':
                pretty_name = '<' + pretty_name[1:] + '> '
            pretty_name = pretty_name + '", url: "' + link % (row[2])
        data = re.sub(r'\n { label: "(.*?)"},', r'''\n { label: "no parent >> \1"},''', res)
        context['data'] = data
        return context
