
import sys

def setquery(type, location, qualifier):

    if type == 'inventory':

        return """
SELECT distinct on (locationkey,sortableobjectnumber,h3.name)
(case when ca.computedcrate is Null then l.termdisplayName
     else concat(l.termdisplayName,
     ': ',regexp_replace(ca.computedcrate, '^.*\\)''(.*)''$', '\\1')) end) AS storageLocation,
replace(concat(l.termdisplayName,
     ': ',regexp_replace(ca.computedcrate, '^.*\\)''(.*)''$', '\\1')),' ','0') AS locationkey,
m.locationdate,
cc.objectnumber objectnumber,
cc.numberofobjects objectCount,
(case when ong.objectName is NULL then '' else ong.objectName end) objectName,
rc.subjectcsid movementCsid,
lc.refname movementRefname,
rc.objectcsid  objectCsid,
''  objectRefname,
m.id moveid,
rc.subjectdocumenttype,
rc.objectdocumenttype,
cp.sortableobjectnumber sortableobjectnumber,
ca.computedcrate crateRefname,
regexp_replace(ca.computedcrate, '^.*\\)''(.*)''$', '\\1') crate

FROM loctermgroup l

join hierarchy h1 on l.id = h1.id
join locations_common lc on lc.id = h1.parentid
join movements_common m on m.currentlocation = lc.refname

join hierarchy h2 on m.id = h2.id
join relations_common rc on rc.subjectcsid = h2.name

join hierarchy h3 on rc.objectcsid = h3.name
join collectionobjects_common cc on (h3.id = cc.id and cc.computedcurrentlocation = lc.refname)

left outer join collectionobjects_anthropology ca on (ca.id=cc.id)
left outer join hierarchy h5 on (cc.id = h5.parentid and h5.name = 'collectionobjects_common:objectNameList' and h5.pos=0)
left outer join objectnamegroup ong on (ong.id=h5.id)

left outer join collectionobjects_pahma cp on (cp.id=cc.id)

join misc ms on (cc.id=ms.id and ms.lifecyclestate <> 'deleted')

WHERE
   l.termdisplayName = '""" + str(location) + """'

ORDER BY locationkey,sortableobjectnumber,h3.name desc
LIMIT 30000"""

    elif type == 'keyinfo' or type == 'barcodeprint' or type == 'packinglist':

            return """
SELECT distinct on (locationkey,sortableobjectnumber,h3.name)
(case when ca.computedcrate is Null then l.termdisplayName
     else concat(l.termdisplayName,
     ': ',regexp_replace(ca.computedcrate, '^.*\\)''(.*)''$', '\\1')) end) AS storageLocation,
replace(concat(l.termdisplayName,
     ': ',regexp_replace(ca.computedcrate, '^.*\\)''(.*)''$', '\\1')),' ','0') AS locationkey,
m.locationdate,
cc.objectnumber objectnumber,
(case when ong.objectName is NULL then '' else ong.objectName end) objectName,
cc.numberofobjects objectCount,
case when (pfc.item is not null and pfc.item <> '') then
substring(pfc.item, position(')''' IN pfc.item)+2, LENGTH(pfc.item)-position(')''' IN pfc.item)-2)
end AS fieldcollectionplace,
case when (apg.assocpeople is not null and apg.assocpeople <> '') then
substring(apg.assocpeople, position(')''' IN apg.assocpeople)+2, LENGTH(apg.assocpeople)-position(')''' IN apg.assocpeople)-2)
end as culturalgroup,
rc.objectcsid  objectCsid,
case when (pef.item is not null and pef.item <> '') then
substring(pef.item, position(')''' IN pef.item)+2, LENGTH(pef.item)-position(')''' IN pef.item)-2)
end as ethnographicfilecode,
pfc.item fcpRefName,
apg.assocpeople cgRefName,
pef.item efcRefName,
ca.computedcrate,
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
rd.item

FROM loctermgroup l

join hierarchy h1 on l.id = h1.id
join locations_common lc on lc.id = h1.parentid
join movements_common m on m.currentlocation = lc.refname

join hierarchy h2 on m.id = h2.id
join relations_common rc on rc.subjectcsid = h2.name

join hierarchy h3 on rc.objectcsid = h3.name
join collectionobjects_common cc on (h3.id = cc.id and cc.computedcurrentlocation = lc.refname)

left outer join hierarchy h4 on (cc.id = h4.parentid and h4.name = 'collectionobjects_common:objectNameList' and (h4.pos=0 or h4.pos is null))
left outer join objectnamegroup ong on (ong.id=h4.id)

left outer join collectionobjects_anthropology ca on (ca.id=cc.id)
left outer join collectionobjects_pahma cp on (cp.id=cc.id)
left outer join collectionobjects_pahma_pahmafieldcollectionplacelist pfc on (pfc.id=cc.id and (pfc.pos=0 or pfc.pos is null))
left outer join collectionobjects_pahma_pahmaethnographicfilecodelist pef on (pef.id=cc.id and (pef.pos=0 or pef.pos is null))

left outer join hierarchy h5 on (cc.id=h5.parentid and h5.primarytype = 'assocPeopleGroup' and (h5.pos=0 or h5.pos is null))
left outer join assocpeoplegroup apg on (apg.id=h5.id)

left outer join collectionobjects_common_briefdescriptions bd on (bd.id=cc.id and bd.pos=0)
left outer join collectionobjects_common_fieldcollectors pc on (pc.id=cc.id and pc.pos=0)

FULL OUTER JOIN hierarchy h6 ON (h6.id = cc.id)
FULL OUTER JOIN relations_common rc6 ON (rc6.subjectcsid = h6.name AND rc6.objectdocumenttype = 'Acquisition')

FULL OUTER JOIN hierarchy h7 ON (h7.name = rc6.objectcsid)
FULL OUTER JOIN acquisitions_common ac ON (ac.id = h7.id)
FULL OUTER JOIN hierarchy h9 ON (ac.id = h9.id)
FULL OUTER JOIN acquisitions_common_owners donor ON (ac.id = donor.id AND (donor.pos = 0 OR donor.pos IS NULL))
FULL OUTER JOIN misc msac ON (ac.id = msac.id AND msac.lifecyclestate <> 'deleted')

FULL OUTER JOIN hierarchy h8 ON (cc.id = h8.parentid AND h8.name = 'collectionobjects_pahma:pahmaAltNumGroupList' AND (h8.pos = 0 OR h8.pos IS NULL))
FULL OUTER JOIN pahmaaltnumgroup an ON (h8.id = an.id)

join misc ms on (cc.id=ms.id and ms.lifecyclestate <> 'deleted')

left outer join collectionobjects_common_responsibledepartments rd on (rd.id=cc.id and rd.pos=0)

WHERE
   l.termdisplayName = '""" + str(location) + """'


ORDER BY locationkey,sortableobjectnumber,h3.name desc
LIMIT 30000
"""


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

    elif type == 'getobjlist':

        return """SELECT DISTINCT ON (sortableobjectnumber)
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
    %s
    ORDER BY sortableobjectnumber
    limit 5000"""

    elif type == 'getsortableobjno':
        return """
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


if __name__ == "__main__":

    print "compiles OK"