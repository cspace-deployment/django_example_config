#!/usr/bin/env /usr/bin/python

import time
import sys
import psycopg2
from setquery import setquery

reload(sys)
sys.setdefaultencoding('utf-8')

timeoutcommand = "set statement_timeout to 1200000; SET NAMES 'utf8';"

from utils import institution, connect_string

dbconn = psycopg2.connect(connect_string)
cursor = dbconn.cursor()
cursor.execute(timeoutcommand)

def testDB(cursor):
    try:
        cursor.execute('set statement_timeout to 5000')
        cursor.execute('select * from hierarchy limit 30000')
        return "OK"
    except psycopg2.DatabaseError, e:
        sys.stderr.write('testDB error: %s' % e)
        return '%s' % e
    except:
        sys.stderr.write("some other testDB error!")
        return "Some other failure"


def dbtransaction(command):
    cursor.execute(command)


def getlocations(location1, location2, num2ret, updateType, institution):

    debug = False

    result = []

    for loc in getloclist('set', location1, '', num2ret):
        getobjects = setquery(updateType, loc[0], '', institution)

        sys.stderr.write("getloclist %s" % location1)

        try:
            elapsedtime = time.time()
            cursor.execute(getobjects)
            elapsedtime = time.time() - elapsedtime
            if debug: sys.stderr.write('all objects: %s :: %s\n' % (loc[0], elapsedtime))
        except psycopg2.DatabaseError, e:
            sys.stderr.write('getlocations select error: %s' % e)
            #return result
            raise
        except:
            sys.stderr.write("some other getlocations database error!")
            #return result
            raise

        try:
            rows = [list(item) for item in cursor.fetchall()]
        except psycopg2.DatabaseError, e:
            sys.stderr.write("fetchall getlocations database error!")

        if debug: sys.stderr.write('number objects to be checked: %s\n' % len(rows))
        try:
            for row in rows:
                result.append(row)
        except:
            sys.stderr.write("other getobjects error: %s" % len(rows))
            raise

    return result


def getplants(location1, location2, num2ret, updateType, qualifier):

    debug = False

    result = []

    #for loc in getloclist('set',location1,'',num2ret,config):
    getobjects = setquery(updateType, location1, qualifier, 'ucbg')
    #print "<span>%s</span>" % getobjects
    try:
        elapsedtime = time.time()
        cursor.execute(getobjects)
        elapsedtime = time.time() - elapsedtime
        #sys.stderr.write('query :: %s\n' % getobjects)
        if debug: sys.stderr.write('all objects: %s :: %s\n' % (location1, elapsedtime))
    except psycopg2.DatabaseError, e:
        raise
        #sys.stderr.write('getplants select error: %s' % e)
        #return result
    except:
        sys.stderr.write("some other getplants database error!")
        return result

    try:
        result = [list(item) for item in cursor.fetchall()]
        if debug: sys.stderr.write('object count: %s\n' % (len(result)))
    except psycopg2.DatabaseError, e:
        sys.stderr.write("fetchall getplants database error!")

    return result


def getloclist(searchType, location1, location2, num2ret):
    # 'set' means 'next num2ret locations', otherwise prefix match
    if searchType == 'set':
        whereclause = "WHERE locationkey >= replace('" + location1 + "',' ','0')"
    elif searchType == 'exact':
        whereclause = "WHERE locationkey = replace('" + location1 + "',' ','0')"
    elif searchType == 'prefix':
        whereclause = "WHERE locationkey LIKE replace('" + location1 + "%',' ','0')"
    elif searchType == 'range':
        whereclause = "WHERE locationkey >= replace('" + location1 + "',' ','0') AND locationkey <= replace('" + location2 + "',' ','0')"

    if int(num2ret) > 30000: num2ret = 30000
    if int(num2ret) < 1:    num2ret = 1

    getobjects = """
select * from (
select termdisplayname,replace(termdisplayname,' ','0') locationkey 
FROM loctermgroup ltg
INNER JOIN hierarchy h_ltg
        ON h_ltg.id=ltg.id
INNER JOIN hierarchy h_loc
        ON h_loc.id=h_ltg.parentid
INNER JOIN misc
        ON misc.id=h_loc.id and misc.lifecyclestate <> 'deleted'
) as t
""" + whereclause + """
order by locationkey
limit """ + str(num2ret)

    try:
        cursor.execute(getobjects)
        #for object in objects.fetchall():
        #print object
        # return objects.fetchall()
        return [list(item) for item in cursor.fetchall()]
    except:
        raise


def getobjlist(searchType, object1, object2, num2ret):
    query1 = """
    SELECT objectNumber,
cp.sortableobjectnumber
FROM collectionobjects_common cc
left outer join collectionobjects_pahma cp on (cp.id=cc.id)
INNER JOIN hierarchy h1
        ON cc.id=h1.id
INNER JOIN misc
        ON misc.id=h1.id and misc.lifecyclestate <> 'deleted'
WHERE
     cc.objectNumber = '%s'"""

    if int(num2ret) > 1000: num2ret = 1000
    if int(num2ret) < 1:    num2ret = 1

    cursor.execute(query1 % object1)
    (object1, sortkey1) = cursor.fetchone()
    cursor.execute(query1 % object2)
    (object2, sortkey2) = cursor.fetchone()

    # 'set' means 'next num2ret objects', otherwise prefix match
    if searchType == 'set':
        whereclause = "WHERE sortableobjectnumber >= '" + sortkey1 + "'"
    elif searchType == 'prefix':
        whereclause = "WHERE sortableobjectnumber LIKE '" + sortkey1 + "%'"
    elif searchType == 'range':
        whereclause = "WHERE sortableobjectnumber >= '" + sortkey1 + "' AND sortableobjectnumber <= '" + sortkey2 + "'"

    getobjects = """SELECT DISTINCT ON (sortableobjectnumber)
(case when ca.computedcrate is Null then regexp_replace(cc.computedcurrentlocation, '^.*\\)''(.*)''$', '\\1') 
     else concat(regexp_replace(cc.computedcurrentlocation, '^.*\\)''(.*)''$', '\\1'),
     ': ',regexp_replace(ca.computedcrate, '^.*\\)''(.*)''$', '\\1')) end) AS storageLocation,
cc.computedcurrentlocation AS locrefname,
'' AS locdate,
cc.objectnumber objectnumber,
(case when ong.objectName is NULL then '' else regexp_replace(ong.objectName, '^.*\\)''(.*)''$', '\\1') end) objectName,
cc.numberofobjects objectCount,
case when (pfc.item is not null and pfc.item <> '') then
 substring(pfc.item, position(')''' IN pfc.item)+2, LENGTH(pfc.item)-position(')''' IN pfc.item)-2)
end AS fieldcollectionplace,
case when (apg.assocpeople is not null and apg.assocpeople <> '') then
 substring(apg.assocpeople, position(')''' IN apg.assocpeople)+2, LENGTH(apg.assocpeople)-position(')''' IN apg.assocpeople)-2)
end as culturalgroup,
h1.name  objectCsid,
case when (pef.item is not null and pef.item <> '') then
 substring(pef.item, position(')''' IN pef.item)+2, LENGTH(pef.item)-position(')''' IN pef.item)-2)
end as ethnographicfilecode,
pfc.item fcpRefName,
apg.assocpeople cgRefName,
pef.item efcRefName,
ca.computedcrate crateRefname,
regexp_replace(ca.computedcrate, '^.*\\)''(.*)''$', '\\1') crate,
case when (bd.item is not null and bd.item <> '') then
bd.item end as briefdescription,
case when (pc.item is not null and pc.item <> '') then
substring(pc.item, position(')''' IN pc.item)+2, LENGTH(pc.item)-position(')''' IN pc.item)-2)
end as fieldcollector,
case when (donor.item is not null and donor.item <> '') then
substring(donor.item, position(')''' IN donor.item)+2, LENGTH(donor.item)-position(')''' IN donor.item)-2)
end as donor,
case when (an.pahmaaltnum is not null and an.pahmaaltnum <> '') then
an.pahmaaltnum end as altnum,
case when (an.pahmaaltnumtype is not null and an.pahmaaltnumtype <> '') then
an.pahmaaltnumtype end as altnumtype,
pc.item pcRefName,
ac.acquisitionreferencenumber accNum,
donor.item pdRefName,
ac.id accID,
h9.name accCSID,
cp.inventoryCount,
cc.collection,
rd.item,
cp.pahmafieldlocverbatim,
fcd.datedisplaydate

FROM collectionobjects_pahma cp
left outer join collectionobjects_common cc on (cp.id=cc.id)

left outer join hierarchy h1 on (cp.id = h1.id)

left outer join hierarchy h4 on (cc.id = h4.parentid and h4.name =
'collectionobjects_common:objectNameList' and (h4.pos=0 or h4.pos is null))
left outer join objectnamegroup ong on (ong.id=h4.id)

left outer join collectionobjects_anthropology ca on (ca.id=cc.id)
left outer join collectionobjects_pahma_pahmafieldcollectionplacelist pfc on (pfc.id=cc.id and pfc.pos=0)
left outer join collectionobjects_pahma_pahmaethnographicfilecodelist pef on (pef.id=cc.id and pef.pos=0)

left outer join hierarchy h5 on (cc.id=h5.parentid and h5.primarytype =
'assocPeopleGroup' and (h5.pos=0 or h5.pos is null))
left outer join assocpeoplegroup apg on (apg.id=h5.id)
 
left outer join collectionobjects_common_briefdescriptions bd on (bd.id=cc.id and bd.pos=0)
left outer join collectionobjects_common_fieldcollectors pc on (pc.id=cc.id and pc.pos=0)

FULL OUTER JOIN relations_common rc6 ON (rc6.subjectcsid = h1.name AND rc6.objectdocumenttype = 'Acquisition')
FULL OUTER JOIN hierarchy h7 ON (h7.name = rc6.objectcsid)
FULL OUTER JOIN acquisitions_common ac ON (ac.id = h7.id)
FULL OUTER JOIN hierarchy h9 ON (ac.id = h9.id)
FULL OUTER JOIN acquisitions_common_owners donor ON (ac.id = donor.id AND (donor.pos = 0 OR donor.pos IS NULL))
FULL OUTER JOIN misc msac ON (ac.id = msac.id AND msac.lifecyclestate <> 'deleted')

FULL OUTER JOIN hierarchy h8 ON (cc.id = h8.parentid AND h8.name = 'collectionobjects_pahma:pahmaAltNumGroupList' AND (h8.pos = 0 OR h8.pos IS NULL))
FULL OUTER JOIN pahmaaltnumgroup an ON (h8.id = an.id)

FULL OUTER JOIN hierarchy h10 ON (h10.parentid = cc.id AND h10.pos = 0 AND h10.name = 'collectionobjects_pahma:pahmaFieldCollectionDateGroupList')
FULL OUTER JOIN structureddategroup fcd ON (fcd.id = h10.id)
 
join misc ms on (cc.id=ms.id and ms.lifecyclestate <> 'deleted')

left outer join collectionobjects_common_responsibledepartments rd on (rd.id=cc.id and rd.pos=0)
""" + whereclause + """
ORDER BY sortableobjectnumber
limit """ + str(num2ret)

    cursor.execute(getobjects)
    #for object in objects.fetchall():
    #print object
    # return objects.fetchall()
    return [list(item) for item in cursor.fetchall()]


def findcurrentlocation(csid):

    getloc = "select findcurrentlocation('" + csid + "')"

    try:
        cursor.execute(getloc)
    except:
        return "findcurrentlocation error"

    return cursor.fetchone()[0]


def getrefname(table, term):

    if term == None or term == '':
        return ''

    if table in ('collectionobjects_common_fieldcollectors', 'collectionobjects_common_briefdescriptions',
                 'acquisitions_common_owners'):
        column = 'item'
    else:
        column = 'refname'

    if table == 'collectionobjects_common_briefdescriptions':
        query = "SELECT item FROM collectionobjects_common_briefdescriptions WHERE item ILIKE '%s' LIMIT 1" % (
            term.replace("'", "''"))
    elif table == 'pahmaaltnumgroup':
        query = "SELECT pahmaaltnum FROM pahmaaltnumgroup WHERE pahmaaltnum ILIKE '%s' LIMIT 1" % (
            term.replace("'", "''"))
    elif table == 'pahmaaltnumgroup_type':
        query = "SELECT pahmaaltnumtype FROM pahmaaltnumgroup WHERE pahmaaltnum ILIKE '%s' LIMIT 1" % (
            term.replace("'", "''"))
    else:
        query = "select %s from %s where %s ILIKE '%%''%s''%%' LIMIT 1" % (
            column, table, column, term.replace("'", "''"))

    try:
        cursor.execute(query)
        return cursor.fetchone()[0]
    except:
        return ''
        raise


def findrefnames(table, termlist):

    result = []
    for t in termlist:
        query = "select refname from %s where refname ILIKE '%%''%s''%%'" % (table, t.replace("'", "''"))

        try:
            cursor.execute(query)
            refname = cursor.fetchone()
            result.append([t, refname])
        except:
            raise
            return "findrefnames error"

    return result

def finddoctypes(table, doctype):
    query = "select %s,count(*) as n from %s group by %s;" % (doctype,table,doctype)

    try:
        cursor.execute(query)
        # return doctypes.fetchall()
        return [list(item) for item in cursor.fetchall()]
    except:
        raise
        return "finddoctypes error"


def getobjinfo(museumNumber):

    getobjects = """
    SELECT co.objectnumber,
    n.objectname,
    co.numberofobjects,
    regexp_replace(fcp.item, '^.*\\)''(.*)''$', '\\1') AS fieldcollectionplace,
    regexp_replace(apg.assocpeople, '^.*\\)''(.*)''$', '\\1') AS culturalgroup,
    regexp_replace(pef.item, '^.*\\)''(.*)''$', '\\1') AS  ethnographicfilecode
FROM collectionobjects_common co
LEFT OUTER JOIN hierarchy h1 ON (co.id = h1.parentid AND h1.primarytype='objectNameGroup' AND h1.pos=0)
LEFT OUTER JOIN objectnamegroup n ON (n.id=h1.id)
LEFT OUTER JOIN collectionobjects_pahma_pahmafieldcollectionplacelist fcp ON (co.id=fcp.id AND fcp.pos=0)
LEFT OUTER JOIN collectionobjects_pahma_pahmaethnographicfilecodelist pef on (pef.id=co.id and pef.pos=0)
LEFT OUTER JOIN collectionobjects_common_responsibledepartments cm ON (co.id=cm.id AND cm.pos=0)
LEFT OUTER JOIN hierarchy h2 ON (co.id=h2.parentid AND h2.primarytype='assocPeopleGroup' AND h2.pos=0)
LEFT OUTER JOIN assocpeoplegroup apg ON apg.id=h2.id
JOIN misc ON misc.id = co.id AND misc.lifecyclestate <> 'deleted'
WHERE co.objectnumber = '%s' LIMIT 1""" % museumNumber

    cursor.execute(getobjects)
    #for ob in objects.fetchone():
    #print ob
    return cursor.fetchone()


def gethierarchy(query):

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

    cursor.execute(gethierarchy)
    #return cursor.fetchall()
    return [list(item) for item in cursor.fetchall()]


def getCSID(argType, arg):

    if argType == 'objectnumber':
        query = """SELECT h.name from collectionobjects_common cc
JOIN hierarchy h on h.id=cc.id
WHERE objectnumber = '%s'""" % arg.replace("'", "''")
    elif argType == 'crateName':
        query = """SELECT h.name FROM collectionobjects_anthropology ca
JOIN hierarchy h on h.id=ca.id
WHERE computedcrate ILIKE '%%''%s''%%'""" % arg.replace("'", "''")
    elif argType == 'placeName':
        query = """SELECT h.name from places_common pc
JOIN hierarchy h on h.id=pc.id
WHERE pc.refname ILIKE '%""" + arg.replace("'", "''") + "%%'"

    cursor.execute(query)
    return cursor.fetchone()


def getCSIDs(argType, arg):

    if argType == 'crateName':
        query = """SELECT h.name FROM collectionobjects_anthropology ca
JOIN hierarchy h on h.id=ca.id
WHERE computedcrate ILIKE '%%''%s''%%'""" % arg.replace("'", "''")

    cursor.execute(query)
    # return cursor.fetchall()
    return [list(item) for item in cursor.fetchall()]


def findparents(refname):

    query = """WITH RECURSIVE ethnculture_hierarchyquery as (
SELECT regexp_replace(cc.refname, '^.*\\)''(.*)''$', '\\1') AS ethnCulture,
      cc.refname,
      rc.objectcsid broaderculturecsid,
      regexp_replace(cc2.refname, '^.*\\)''(.*)''$', '\\1') AS ethnCultureBroader,
      0 AS level
FROM concepts_common cc
JOIN hierarchy h ON (cc.id = h.id)
LEFT OUTER JOIN relations_common rc ON (h.name = rc.subjectcsid)
LEFT OUTER JOIN hierarchy h2 ON (rc.relationshiptype='hasBroader' AND rc.objectcsid = h2.name)
LEFT OUTER JOIN concepts_common cc2 ON (cc2.id = h2.id)
WHERE cc.refname LIKE 'urn:cspace:pahma.cspace.berkeley.edu:conceptauthorities:name(concept)%%'
and cc.refname = '%s'
UNION ALL
SELECT regexp_replace(cc.refname, '^.*\\)''(.*)''$', '\\1') AS ethnCulture,
      cc.refname,
      rc.objectcsid broaderculturecsid,
      regexp_replace(cc2.refname, '^.*\\)''(.*)''$', '\\1') AS ethnCultureBroader,
      ech.level-1 AS level
FROM concepts_common cc
JOIN hierarchy h ON (cc.id = h.id)
LEFT OUTER JOIN relations_common rc ON (h.name = rc.subjectcsid)
LEFT OUTER JOIN hierarchy h2 ON (rc.relationshiptype='hasBroader' AND rc.objectcsid = h2.name)
LEFT OUTER JOIN concepts_common cc2 ON (cc2.id = h2.id)
INNER JOIN ethnculture_hierarchyquery AS ech ON h.name = ech.broaderculturecsid)
SELECT ethnCulture, refname, level
FROM ethnculture_hierarchyquery
order by level""" % refname.replace("'", "''")

    try:
        cursor.execute(query)
        # return cursor.fetchall()
        return [list(item) for item in cursor.fetchall()]
    except:
        #raise
        return [["findparents error"]]

def getCSIDDetail(config, csid, detail):

    
    if detail == 'fieldcollectionplace':
        query = """SELECT substring(pfc.item, position(')''' IN pfc.item)+2, LENGTH(pfc.item)-position(')''' IN pfc.item)-2)
AS fieldcollectionplace

FROM collectionobjects_pahma_pahmafieldcollectionplacelist pfc
LEFT OUTER JOIN HIERARCHY h1 on (pfc.id=h1.id and pfc.pos = 0)

WHERE h1.name = '%s'""" % csid
    elif detail == 'assocpeoplegroup':
        query = """SELECT substring(apg.assocpeople, position(')''' IN apg.assocpeople)+2, LENGTH(apg.assocpeople)-position(')''' IN apg.assocpeople)-2)
as culturalgroup

FROM collectionobjects_common cc

left outer join hierarchy h1 on (cc.id=h1.id)
left outer join hierarchy h2 on (cc.id=h2.parentid and h2.primarytype =
'assocPeopleGroup' and (h2.pos=0 or h2.pos is null))
left outer join assocpeoplegroup apg on (apg.id=h2.id)

WHERE h1.name = '%s'""" % csid
    elif detail == 'objcount':
        query = """SELECT cc.numberofobjects
FROM collectionobjects_common cc
left outer join hierarchy h1 on (cc.id=h1.id)
WHERE h1.name = '%s'""" % csid
    elif detail == 'objNumber':
        query = """SELECT cc.objectnumber
FROM collectionobjects_common cc
left outer join hierarchy h1 on (cc.id=h1.id)
WHERE h1.name = '%s'""" % csid
    else:
        return ''
    try:
        cursor.execute(query)
        return cursor.fetchone()[0]
    except:
        return ''

def checkData(config, data, datatype):

    if datatype == "objno":
        query = """SELECT
EXISTS(SELECT cc.objectnumber AS objno
FROM collectionobjects_common cc
JOIN misc ON (cc.id=misc.id)
WHERE misc.lifecyclestate <> 'deleted'
AND cc.objectnumber='%s')""" % data
    if datatype in ["crate", "location"]:
        query = """SELECT
EXISTS(SELECT lc.refname
FROM locations_common lc
JOIN misc ON (lc.id=misc.id)
WHERE misc.lifecyclestate <> 'deleted'
AND lc.refname LIKE 'urn:cspace:pahma.cspace.berkeley.edu:locationauthorities:name(""" + datatype + """):%""" + data + """''')"""
    cursor.execute(query)
    return cursor.fetchone()

def getSitesByOwner(config, owner):

    query = """SELECT DISTINCT REGEXP_REPLACE(fcp.item, '^.*\)''(.*)''$', '\\1') AS "site",
    REGEXP_REPLACE(pog.anthropologyplaceowner, '^.*\)''(.*)''$', '\\1') AS "site owner",
    pog.anthropologyplaceownershipnote AS "ownership note",
    pc.placenote AS "place note"
FROM collectionobjects_pahma_pahmafieldcollectionplacelist fcp 
JOIN places_common pc ON (pc.refname = fcp.item)
JOIN misc ms ON (ms.id = pc.id AND ms.lifecyclestate <> 'deleted')
JOIN hierarchy h1 ON (h1.parentid = pc.id AND h1.name = 'places_anthropology:anthropologyPlaceOwnerGroupList')
JOIN anthropologyplaceownergroup pog ON (pog.id = h1.id)
WHERE pog.anthropologyplaceowner LIKE '%%""" + owner.replace("'", "''") + """%%'
ORDER BY REGEXP_REPLACE(fcp.item, '^.*\)''(.*)''$', '\\1')"""
    cursor.execute(query)
    # return cursor.fetchall()
    return [list(item) for item in cursor.fetchall()]


def getDisplayName(config, refname):

    query = """SELECT REGEXP_REPLACE(pog.anthropologyplaceowner, '^.*\)''(.*)''$', '\\1')
FROM anthropologyplaceownergroup pog
WHERE pog.anthropologyplaceowner LIKE '""" + refname + "%'"
    
    cursor.execute(query)
    return cursor.fetchone()

def getObjDetailsByOwner(config, owner):

    query = """SELECT DISTINCT cc.objectnumber AS "Museum No.",
    cp.sortableobjectnumber AS "sort number",
    cc.numberofobjects AS "pieces",
    ong.objectname AS "object name",
    fcd.datedisplaydate AS "collection date",
    STRING_AGG(DISTINCT(ac.acquisitionreferencenumber), ', ') AS "Acc. No.",
    REGEXP_REPLACE(fcp.item, '^.*\)''(.*)''$', '\\1') AS "site",
    REGEXP_REPLACE(pog.anthropologyplaceowner, '^.*\)''(.*)''$', '\\1') AS "site owner",
    pog.anthropologyplaceownershipnote AS "ownership note", pc.placenote AS "place note"
FROM collectionobjects_common cc
JOIN collectionobjects_pahma cp ON (cc.id = cp.id)
JOIN collectionobjects_pahma_pahmafieldcollectionplacelist fcp ON (fcp.id = cc.id)
JOIN misc ms ON (ms.id = cc.id AND ms.lifecyclestate <> 'deleted')
JOIN places_common pc ON (pc.refname = fcp.item)
JOIN hierarchy h1 ON (h1.parentid = pc.id AND h1.name = 'places_anthropology:anthropologyPlaceOwnerGroupList')
JOIN anthropologyplaceownergroup pog ON (pog.id = h1.id)
FULL OUTER JOIN hierarchy h2 ON (h2.parentid = cc.id AND h2.name = 'collectionobjects_common:objectNameList' AND h2.pos = 0)
FULL OUTER JOIN objectnamegroup ong ON (ong.id = h2.id)
FULL OUTER JOIN hierarchy h3 ON (h3.id = cc.id)
FULL OUTER JOIN relations_common rc ON (rc.subjectcsid = h3.name AND rc.objectdocumenttype = 'Acquisition')
FULL OUTER JOIN hierarchy h4 ON (h4.name = rc.objectcsid)
FULL OUTER JOIN acquisitions_common ac ON (ac.id = h4.id)
FULL OUTER JOIN hierarchy h5 ON (h5.parentid = cc.id AND h5.pos = 0 AND h5.name = 'collectioncursor_pahma:pahmaFieldCollectionDateGroupList')
FULL OUTER JOIN structureddategroup fcd ON (fcd.id = h5.id)
WHERE REGEXP_REPLACE(pog.anthropologyplaceowner, '^.*\)''(.*)''$', '\\1') ILIKE '%""" + owner + """%'
OR (pog.anthropologyplaceowner IS NULL AND pog.anthropologyplaceownershipnote ILIKE '%""" + owner + """%')
GROUP BY cc.objectnumber, cp.sortableobjectnumber, cc.numberofobjects, ong.objectname, fcd.datedisplaydate, fcp.item, pog.anthropologyplaceowner, pog.anthropologyplaceownershipnote, pc.placenote
ORDER BY REGEXP_REPLACE(fcp.item, '^.*\)''(.*)''$', '\\1'), pog.anthropologyplaceownershipnote, cp.sortableobjectnumber
"""

    cursor.execute(query)
    # return cursor.fetchall()
    return [list(item) for item in cursor.fetchall()]


if __name__ == "__main__":

    print "compiles OK"