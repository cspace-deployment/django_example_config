#!/usr/bin/env /usr/bin/python

import sys

def setquery(type, location, qualifier):

    if type == 'inventory':

        return """
SELECT distinct on (locationkey,h3.name)
l.termdisplayName  AS storageLocation,
replace(l.termdisplayName,' ','0') AS locationkey,
m.locationdate,
cc.objectnumber objectnumber,
cc.numberofobjects objectCount,
(case when ong.objectName is NULL then '' else regexp_replace(ong.objectName, '^.*\\)''(.*)''$', '\\1') end) objectName,
rc.subjectcsid movementCsid,
lc.refname movementRefname,
rc.objectcsid  objectCsid,
''  objectRefname,
m.id moveid,
rc.subjectdocumenttype,
rc.objectdocumenttype,
l.termdisplayName AS sortableobjectnumber,
'' AS crateRefname,
'' AS crate

FROM loctermgroup l

join hierarchy h1 on l.id = h1.id
join locations_common lc on lc.id = h1.parentid
join movements_common m on m.currentlocation = lc.refname

join hierarchy h2 on m.id = h2.id
join relations_common rc on rc.subjectcsid = h2.name

join hierarchy h3 on rc.objectcsid = h3.name
join collectionobjects_common cc on (h3.id = cc.id and cc.computedcurrentlocation = lc.refname)

left outer join hierarchy h5 on (cc.id = h5.parentid and h5.name = 'collectionobjects_common:objectNameList' and h5.pos=0)
left outer join objectnamegroup ong on (ong.id=h5.id)

join misc ms on (cc.id=ms.id and ms.lifecyclestate <> 'deleted')

WHERE 
   l.termdisplayName = '""" + str(location) + """'
   
ORDER BY locationkey,h3.name desc
LIMIT 30000"""

    elif type == 'bedlist' or type == 'locreport' or type == 'keyinfo' or type == 'barcodeprint' or type == 'packinglist':

        if type == 'locreport':
            sortkey = 'determination'
            searchkey = 'tig.taxon'
        else:
            sortkey = 'gardenlocation'
            searchkey = 'lct.termdisplayname'

        queryTemplate = """
select distinct on (to_number(objectnumber,'9999.9999'))
case when (mc.currentlocation is not null and mc.currentlocation <> '') then regexp_replace(mc.currentlocation, '^.*\\)''(.*)''$', '\\1') end as gardenlocation,
lct.termname shortgardenlocation,
case when (lc.locationtype is not null and lc.locationtype <> '') then regexp_replace(lc.locationtype, '^.*\\)''(.*)''$', '\\1') end as locationtype,
co1.recordstatus,
co1.objectnumber,
findhybridaffinname(tig.id) as determination,
case when (tn.family is not null and tn.family <> '') then regexp_replace(tn.family, '^.*\\)''(.*)''$', '\\1') end as family,
h1.name as objectcsid,
con.rare,
cob.deadflag,
case when (tn.family is not null and tn.family <> '') then regexp_replace(tn.family, '^.*\\)''(.*)''$', '\\1') end as family,
-- date(mc.locationdate + interval '8 hours') actiondate,
to_char(date(mc.locationdate + interval '8 hours'),'YYYY-MM-DD') AS actiondate,
mc.reasonformove actionreason,
case when (mb.previouslocation is not null and mb.previouslocation <> '') then regexp_replace(mb.previouslocation, '^.*\\)''(.*)''$', '\\1') end as previouslocation 
from collectionobjects_common co1 
join hierarchy h1 on co1.id=h1.id
left outer 
join hierarchy htig on (co1.id = htig.parentid and htig.pos = 0 and htig.name = 'collectionobjects_naturalhistory:taxonomicIdentGroupList')
left outer 
join taxonomicIdentGroup tig on (tig.id = htig.id)
left outer 
join taxon_common tc on (tig.taxon=tc.refname)
left outer 
join taxon_naturalhistory tn on (tc.id=tn.id) 
join relations_common r1 on (h1.name=r1.subjectcsid and objectdocumenttype='Movement') 
join hierarchy h2 on (r1.objectcsid=h2.name and h2.isversion is %s true) 
join movements_common mc on (mc.id=h2.id) 
join movements_botgarden mb on (mc.id=mb.id)
left outer
join loctermgroup lct on (regexp_replace(mc.currentlocation, '^.*\\)''(.*)''$', '\\1')=lct.termdisplayname)
%s
join collectionspace_core core on mc.id=core.id 
join collectionobjects_botgarden cob on (co1.id=cob.id) 
join collectionobjects_naturalhistory con on (co1.id = con.id)

left outer join locations_common lc on (mc.currentlocation=lc.refname) 
where %s  %s = '%s'
ORDER BY to_number(objectnumber,'9999.9999')
LIMIT 1000"""
            
        if qualifier == 'alive':
            queryPart1 = " mc.reasonformove != 'Dead' and "
            queryPart2 = """join misc misc1 on (misc1.id = mc.id and misc1.lifecyclestate <> 'deleted') -- movement not deleted
                            join misc ms on (co1.id=ms.id and ms.lifecyclestate <> 'deleted')"""
            return queryTemplate % ('not', queryPart2, queryPart1, searchkey, location)
        elif qualifier == 'dead':
            queryPart1 = " mc.reasonformove = 'Dead' and "
            queryPart2 = "inner join misc misc1 on (misc1.id = mc.id and misc1.lifecyclestate <> 'deleted') -- movement not deleted"
            return queryTemplate % ('', queryPart2, queryPart1, searchkey, location)
        else:
            print 'no qualifier!'
            return ''
            # houston, we got a problem...query not qualified

    elif type == 'getalltaxa':
        queryTemplate = """
select co1.objectnumber,
findhybridaffinname(tig.id) as determination,
case when (tn.family is not null and tn.family <> '')
     then regexp_replace(tn.family, '^.*\\)''(.*)''$', '\\1')
end as family,
case when (mc.currentlocation is not null and mc.currentlocation <> '')
     then regexp_replace(mc.currentlocation, '^.*\\)''(.*)''$', '\\1')
end as gardenlocation,
co1.recordstatus dataQuality,
case when (lg.fieldlocplace is not null and lg.fieldlocplace <> '') then regexp_replace(lg.fieldlocplace, '^.*\\)''(.*)''$', '\\1')
     when (lg.fieldlocplace is null and lg.taxonomicrange is not null) then 'Geographic range: '||lg.taxonomicrange
end as locality,
h1.name as objectcsid,
con.rare,
cob.deadflag,
regexp_replace(tig2.taxon, '^.*\\)''(.*)''$', '\\1') as determinationNoAuth,
mc.reasonformove,
case when (tn.family is not null and tn.family <> '') then regexp_replace(tn.family, '^.*\\)''(.*)''$', '\\1') end as family,
date(mc.locationdate + interval '8 hours') actiondate,
case when (mb.previouslocation is not null and mb.previouslocation <> '') then regexp_replace(mb.previouslocation, '^.*\\)''(.*)''$', '\\1') end as previouslocation 

from collectionobjects_common co1

join hierarchy h1 on co1.id=h1.id
join relations_common r1 on (h1.name=r1.subjectcsid and objectdocumenttype='Movement')
join hierarchy h2 on (r1.objectcsid=h2.name and h2.isversion is not true)
join movements_common mc on (mc.id=h2.id %s)
join movements_botgarden mb on (mc.id=mb.id)
%s

join collectionobjects_naturalhistory con on (co1.id = con.id)
join collectionobjects_botgarden cob on (co1.id=cob.id)

left outer join hierarchy htig
     on (co1.id = htig.parentid and htig.pos = 0 and htig.name = 'collectionobjects_naturalhistory:taxonomicIdentGroupList')
left outer join taxonomicIdentGroup tig on (tig.id = htig.id)

left outer join hierarchy htig2
     on (co1.id = htig2.parentid and htig2.pos = 1 and htig2.name = 'collectionobjects_naturalhistory:taxonomicIdentGroupList')
left outer join taxonomicIdentGroup tig2 on (tig2.id = htig2.id)

left outer join hierarchy hlg
     on (co1.id = hlg.parentid and hlg.pos = 0 and hlg.name='collectionobjects_naturalhistory:localityGroupList')
left outer join localitygroup lg on (lg.id = hlg.id)

join collectionspace_core core on (core.id=co1.id and core.tenantid=35)
join misc misc2 on (misc2.id = co1.id and misc2.lifecyclestate <> 'deleted') -- object not deleted

left outer join taxon_common tc on (tig.taxon=tc.refname)
left outer join taxon_naturalhistory tn on (tc.id=tn.id) """
        # the form of the query for finding Deads and Alives is a bit different, so we
        # need to build the query string based on what we are trying to make a list of...deads or alives.
        sys.stderr.write('qualifier %s' % qualifier)
        if qualifier == 'alive':
            queryPart1 = ""
            queryPart2 = "join misc misc1 on (misc1.id = mc.id and misc1.lifecyclestate <> 'deleted') -- movement not deleted"
            return queryTemplate % (queryPart1, queryPart2)
        elif qualifier == 'dead':
            queryPart1 = " and mc.reasonformove = 'Dead'"
            queryPart2 = " "
            return queryTemplate % (queryPart1, queryPart2)
        elif qualifier == 'dead or alive':
            queryPart1 = ""
            queryPart2 = "join misc misc1 on (misc1.id = mc.id and misc1.lifecyclestate <> 'deleted') -- movement not deleted"
            part1 = queryTemplate % (queryPart1, queryPart2)
            queryPart1 = " and mc.reasonformove = 'Dead'"
            queryPart2 = " "
            part2 = queryTemplate % (queryPart1, queryPart2)
            return part1 + ' UNION ' + part2
        else:
            print 'no qualifier!'
            return ''
            # houston, we got a problem...query not qualified

    elif type == 'grouplist':

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
hx2.name AS csid,
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

FROM groups_common gc

JOIN misc mc1 ON (gc.id = mc1.id AND mc1.lifecyclestate <> 'deleted')
JOIN hierarchy h1 ON (gc.id=h1.id)
JOIN relations_common rc1 ON (h1.name=rc1.subjectcsid)
JOIN hierarchy hx2 ON (rc1.objectcsid=hx2.name)
JOIN collectionobjects_common cc ON (hx2.id=cc.id)
JOIN collectionobjects_pahma cp on(cp.id = cc.id)

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
WHERE
   gc.title='""" + location + """'
limit 5000"""


if __name__ == "__main__":

    print "compiles OK"