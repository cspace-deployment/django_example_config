#!/usr/bin/env /usr/bin/python

import time
import sys
import cgi
import psycopg2

reload(sys)
sys.setdefaultencoding('utf-8')

timeoutcommand = "set statement_timeout to 1200000; SET NAMES 'utf8';"

def testDB(config):
    dbconn = psycopg2.connect(config.get('connect', 'connect_string'))
    objects = dbconn.cursor()
    try:
        objects.execute('set statement_timeout to 5000')
        objects.execute('select * from hierarchy limit 30000')
        return "OK"
    except psycopg2.DatabaseError, e:
        sys.stderr.write('testDB error: %s' % e)
        return '%s' % e
    except:
        sys.stderr.write("some other testDB error!")
        return "Some other failure"


def dbtransaction(command, config):
    dbconn = psycopg2.connect(config.get('connect', 'connect_string'))
    cursor = dbconn.cursor()
    cursor.execute(command)


def findrefnames(table, termlist, config):
    dbconn = psycopg2.connect(config.get('connect', 'connect_string'))
    objects = dbconn.cursor()
    objects.execute(timeoutcommand)

    result = []
    for t in termlist:
        query = "select refname from %s where refname ILIKE '%%''%s''%%'" % (table, t.replace("'", "''"))

        try:
            objects.execute(query)
            refname = objects.fetchone()
            result.append([t, refname])
        except:
            raise
            return "findrefnames error"

    return result

def finddoctypes(table, doctype, config):
    dbconn = psycopg2.connect(config.get('connect', 'connect_string'))
    doctypes = dbconn.cursor()
    doctypes.execute(timeoutcommand)

    query = "select %s,count(*) as n from %s group by %s;" % (doctype,table,doctype)

    try:
        doctypes.execute(query)
        # return doctypes.fetchall()
        return [list(item) for item in doctypes.fetchall()]
    except:
        raise
        return "finddoctypes error"



def gethierarchy(query, config):
    dbconn = psycopg2.connect(config.get('connect', 'connect_string'))
    institution = config.get('info', 'institution')
    objects = dbconn.cursor()
    objects.execute(timeoutcommand)

    if query == 'taxonomy':
        gethierarchy = """
SELECT DISTINCT
        regexp_replace(child.refname, '^.*\\)''(.*)''$', '\\1') AS Child, 
        regexp_replace(parent.refname, '^.*\\)''(.*)''$', '\\1') AS Parent, 
        h1.name AS ChildKey,
        h2.name AS ParentKey
FROM taxon_common child
JOIN misc ON (misc.id = child.id)
FULL OUTER JOIN hierarchy h1 ON (child.id = h1.id)
FULL OUTER JOIN relations_common rc ON (h1.name = rc.subjectcsid)
FULL OUTER JOIN hierarchy h2 ON (rc.objectcsid = h2.name)
FULL OUTER JOIN taxon_common parent ON (parent.id = h2.id)
WHERE child.refname LIKE 'urn:cspace:%s.cspace.berkeley.edu:taxonomyauthority:name(taxon):item:name%%'
AND misc.lifecyclestate <> 'deleted'
ORDER BY Parent, Child
""" % institution
    elif query != 'places':
        gethierarchy = """
SELECT DISTINCT
        regexp_replace(child.refname, '^.*\\)''(.*)''$', '\\1') AS Child, 
        regexp_replace(parent.refname, '^.*\\)''(.*)''$', '\\1') AS Parent, 
        h1.name AS ChildKey,
        h2.name AS ParentKey
FROM concepts_common child
JOIN misc ON (misc.id = child.id)
FULL OUTER JOIN hierarchy h1 ON (child.id = h1.id)
FULL OUTER JOIN relations_common rc ON (h1.name = rc.subjectcsid)
FULL OUTER JOIN hierarchy h2 ON (rc.objectcsid = h2.name)
FULL OUTER JOIN concepts_common parent ON (parent.id = h2.id)
WHERE child.refname LIKE 'urn:cspace:%s.cspace.berkeley.edu:conceptauthorities:name({0})%%'
AND misc.lifecyclestate <> 'deleted'
ORDER BY Parent, Child""" % institution
        gethierarchy = gethierarchy.format(query)
    else:
        if institution == 'pahma': tenant = 'Tenant15'
        if institution == 'botgarden': tenant = 'Tenant35'
        gethierarchy = """
SELECT DISTINCT
	regexp_replace(tc.refname, '^.*\\)''(.*)''$', '\\1') Place,
	regexp_replace(tc2.refname, '^.*\\)''(.*)''$', '\\1') ParentPlace,
	h.name ChildKey,
	h2.name ParentKey
FROM public.places_common tc
	INNER JOIN misc m ON (tc.id=m.id AND m.lifecyclestate<>'deleted')
	INNER JOIN hierarchy h ON (tc.id = h.id AND h.primarytype='Placeitem%s')
	LEFT OUTER JOIN public.relations_common rc ON (h.name = rc.subjectcsid)
	LEFT OUTER JOIN hierarchy h2 ON (h2.primarytype = 'Placeitem%s' AND rc.objectcsid = h2.name)
	LEFT OUTER JOIN places_common tc2 ON (tc2.id = h2.id)
ORDER BY ParentPlace, Place""" % (tenant, tenant)

    objects.execute(gethierarchy)
    #return objects.fetchall()
    return [list(item) for item in objects.fetchall()]



if __name__ == "__main__":

    from utils import getConfig

    form = {'webapp': 'barcodeprintDev'}

    config = getConfig(form)
    print getobjinfo('1-504', config)

    print '\nkeyinfo\n'
    # Kroeber, 20A, X  1,  1
    # Kroeber, 20AMez, 128 A
    for i, loc in enumerate(getlocations('Kroeber, 20A, X  1,  3', '', 1, config, 'keyinfo','pahma')):
        print 'location', i + 1, loc[0:12]

    sys.exit()


    config = getConfig('sysinvProd.cfg')
    print '\nrefnames\n'
    print getrefname('concepts_common', 'zzz', config)
    print getrefname('concepts_common', '', config)
    print getrefname('concepts_common', 'Yurok', config)
    print findrefnames('places_common', ['zzz', 'Sudan, Northern Africa, Africa'], config)
    print '\ncurrentlocation\n'
    print findcurrentlocation('c65b2ffa-6e5f-4a6d-afa4-e0b57fc16106', config)

    print '\nset of locations\n'
    for loc in getloclist('set', 'Kroeber, 20A, W B', '', 10, config):
        print loc

    print '\nlocations by prefix\n'
    for loc in getloclist('prefix', 'Kroeber, 20A, W B', '', 1000, config):
        print loc

    print '\nlocations by range\n'
    for loc in getloclist('range', 'Kroeber, 20A, W B2, 1', 'Kroeber, 20A, W B5, 11', 1000, config):
        print loc

    print '\nobjects\n'
    for i, loc in enumerate(getlocations('Regatta, A150, South Nexel Unit 6, C', '', 1, config, 'inventory','pahma')):
        print 'location', i + 1, loc[0:6]

    print '\nkeyinfo\n'
    for i, loc in enumerate(getlocations('Kroeber, 20AMez, 128 A', '', 1, config, 'keyinfo','pahma')):
        print 'location', i + 1, loc[0:12]
