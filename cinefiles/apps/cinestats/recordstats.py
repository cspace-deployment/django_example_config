#import psycopg2
import psycopg2
from common import cspace # we use the config file reading function
from os import path


class RecordStats:
    """A simple class to provide the statistical information to populate
       a  cinefiles report.
    """

    def __init__(self):
        config = cspace.getConfig(path.dirname(__file__), 'cinefiles')
        self.DBNAME = config.get('connect', 'dbname')
        self.USER = config.get('connect', 'dbuser')
        self.PW = config.get('connect', 'dbpassword')
        self.SERVER = config.get('connect', 'servername')
        self.MODE = config.get('connect', 'sslmode')
        self.PORT = config.get('connect', 'port')

        # for psycopg2
        self.connect_string = "host=%s port=%s dbname=%s user=%s password=%s sslmode=%s" % (
            self.SERVER, self.PORT, self.DBNAME, self.USER, self.PW, self.MODE)


        # for psycopg2
        #self.connect_string = "%s:%s:%s:%s" % (
        #    self.HOST, self.DBNAME, self.USER, self.PW)

    def getConn(self):
        #conn = psycopg2.connect(self.connect_string)
        conn = psycopg2.connect(self.connect_string)
        return conn

    def getCount(self, query):
        conn = self.getConn()

        if not conn:
            return None

        cur = conn.cursor()
        cur.execute(query)
        res = cur.fetchone()[0]
        cur.close()
        conn.close()
        return res

    def getDocCount(self):
        query = """SELECT count(1)
                 FROM collectionobjects_common cc
                 INNER JOIN misc m 
                    ON (m.id = cc.id
                        AND m.lifecyclestate <> 'deleted'
                        AND cc.collection = 'urn:cspace:cinefiles.cspace.berkeley.edu:vocabularies:name(collection):item:name(cinefiles)''CineFiles''')"""
        return self.getCount(query)

    def getDocYTD(self):
        query = """SELECT count(1)
                 FROM collectionspace_core c
                 INNER JOIN misc m
                    ON (c.id = m.id
                        AND m.lifecyclestate <> 'deleted'
                        AND c.refname like 'urn:cspace:cinefiles.cspace.berkeley.edu:collectionobjects:%'
                        AND  c.createdat > to_date(date_part('year', now())||'-01-01', 'YYYY-MM-DD'))"""
        return self.getCount(query)

    def getNameCount(self):
        query = """SELECT count(1)
                 FROM hierarchy h
                 INNER JOIN persons_common p
                    ON (h.id = p.id 
                        AND p.inauthority = 'ae43b316-d4ff-475f-921c')
                 INNER JOIN misc m
                    ON (h.id = m.id
                        AND m.lifecyclestate <> 'deleted')"""
        return self.getCount(query)

    def getNameYTD(self):
        query = """SELECT count(1)
                 FROM collectionspace_core c
                 INNER JOIN misc m
                    ON (c.id = m.id
                        AND m.lifecyclestate <> 'deleted'
                        AND c.refname like 'urn:cspace:cinefiles.cspace.berkeley.edu:personauthorities:name(person):item:name(%'
                        AND  c.createdat > to_date(date_part('year', now())||'-01-01', 'YYYY-MM-DD'))"""
        return self.getCount(query)

    def getOrgCount(self):
        query = """SELECT count(1)
                 FROM organizations_common oc
                 INNER JOIN misc m
                    ON (oc.id = m.id
                        AND m.lifecyclestate <> 'deleted'
                        AND oc.refname like 'urn:cspace:cinefiles.cspace.berkeley.edu:orgauthorities:name(organization):item:name(%')"""
        return self.getCount(query)

    def getOrgYTD(self):
        query = """SELECT count(1)
                 FROM collectionspace_core c
                 INNER JOIN misc m
                    ON (c.id = m.id
                        AND m.lifecyclestate <> 'deleted'
                        AND c.refname like 'urn:cspace:cinefiles.cspace.berkeley.edu:orgauthorities:name(organization):item:name(%'
                        AND  c.createdat > to_date(date_part('year', now())||'-01-01', 'YYYY-MM-DD'))"""
        return self.getCount(query)

    def getCommitteeCount(self):
        query = """SELECT count(1)
                 FROM organizations_common o
                 INNER JOIN misc m
                    ON (o.id = m.id
                        AND m.lifecyclestate <> 'deleted'
                        AND o.refname like 'urn:cspace:cinefiles.cspace.berkeley.edu:orgauthorities:name(committee):item:name(%')"""
        return self.getCount(query)

    def getCommitteeYTD(self):
        query = """SELECT count(1)
                 FROM collectionspace_core c
                 INNER JOIN misc m
                    ON (c.id = m.id
                        AND m.lifecyclestate <> 'deleted'
                        AND c.refname like 'urn:cspace:cinefiles.cspace.berkeley.edu:orgauthorities:name(committee):item:name(%'
                        AND  c.createdat > to_date(date_part('year', now())||'-01-01', 'YYYY-MM-DD'))"""
        return self.getCount(query)

    def getPageCount(self):
        query = """SELECT sum(numberofobjects)
                 FROM collectionobjects_common cc
                 INNER JOIN misc m
                    ON (cc.id = m.id
                        AND m.lifecyclestate <> 'deleted'
                        AND cc.collection = 'urn:cspace:cinefiles.cspace.berkeley.edu:vocabularies:name(collection):item:name(cinefiles)''CineFiles''')"""
        return self.getCount(query)

    def getPageYTD(self):
        query = """SELECT sum(numberofobjects)
                FROM collectionobjects_common cc
                INNER JOIN misc m
                   ON (cc.id = m.id
                       AND m.lifecyclestate <> 'deleted'
                       AND cc.collection = 'urn:cspace:cinefiles.cspace.berkeley.edu:vocabularies:name(collection):item:name(cinefiles)''CineFiles''')
                INNER JOIN collectionspace_core c
                   ON (c.id = m.id
                       AND c.createdat > to_date(date_part('year', now())||'-01-01', 'YYYY-MM-DD'))"""
        return self.getCount(query)


    def getFilmCount(self):
        query = """SELECT count(1)
                 FROM works_common w
                 INNER JOIN misc m
                    ON (w.id = m.id
                        AND m.lifecyclestate <> 'deleted'
                        AND w.worktype = 'urn:cspace:cinefiles.cspace.berkeley.edu:vocabularies:name(worktype):item:name(film)''Film''')"""
        return self.getCount(query)

    def getFilmYTD(self):
        query = """SELECT count(1)
                 FROM collectionspace_core c
                 INNER JOIN misc m
                    ON (c.id = m.id
                        AND m.lifecyclestate <> 'deleted'
                        AND c.refname like 'urn:cspace:cinefiles.cspace.berkeley.edu:workauthorities:name(work):item:name(pfafilm%'
                        AND  c.createdat > to_date(date_part('year', now())||'-01-01', 'YYYY-MM-DD'))"""
        return self.getCount(query)

    def getSubjectCount(self):
        query = """SELECT count(1)
                 FROM concepts_common c
                 INNER JOIN misc m
                    ON (c.id = m.id
                        AND m.lifecyclestate <> 'deleted'
                        AND c.refname like 'urn:cspace:cinefiles.cspace.berkeley.edu:conceptauthorities:name(concept):item:name(%')"""
        return self.getCount(query)

    def getSubjectYTD(self):
        query = """SELECT count(1)
                 FROM collectionspace_core c
                 INNER JOIN misc m
                    ON (c.id = m.id
                        AND m.lifecyclestate <> 'deleted'
                        AND c.refname like 'urn:cspace:cinefiles.cspace.berkeley.edu:conceptauthorities:name(concept):item:name(%'
                        AND  c.createdat > to_date(date_part('year', now())||'-01-01', 'YYYY-MM-DD')
                        AND  c.createdat > '2014-04-17 11:12:00')"""
        return self.getCount(query)


    def getAccessCounts(self):
        documents = """
            SELECT
                 case when (cc.accesscode is null or cc.accesscode = '')
                   then
                        case when (ocf.accesscode is null or ocf.accesscode = '')
                            then
                                'Not Specified'
                            else
                                ocf.accesscode
                            end
                   else
                     cc.accesscode
                  end as code,
                   sum(co.numberofobjects) pages,
                   count(*) as total
                FROM
                   hierarchy h1
                    JOIN collectionobjects_common co
                      ON (h1.id = co.id AND h1.primarytype = 'CollectionObjectTenant50')
                    JOIN misc m
                      ON (co.id = m.id AND m.lifecyclestate <> 'deleted')
                    JOIN collectionobjects_cinefiles cc
                      ON (co.id = cc.id)
                    JOIN organizations_common oco ON (cc.source=oco.refname)
                    JOIN organizations_cinefiles ocf on (oco.id=ocf.id)

                WHERE (co.objectnumber ~ '^[0-9]+$') and co.recordstatus='approved'
                GROUP BY code"""

        publishers = """
                SELECT
                    case when (ocf.accesscode is null or ocf.accesscode = '')
                        then
                            'Not Specified'
                        else
                            ocf.accesscode
                        end as code,
                   count(*) as total
                FROM
                    organizations_cinefiles ocf
                GROUP BY code
            """

        conn = self.getConn()

        if not conn:
            return None

        cur = conn.cursor()

        cur.execute(publishers)
        publisherCounts = cur.fetchall()
        print publisherCounts

        cur.execute(documents)
        documentCounts = cur.fetchall()
        print documentCounts

        res = {}
        for d in documentCounts:
            res[d[0]] = [d[0], d[1], d[2], 0]
        for d in publisherCounts:
            if d[0] in res:
                if d[0] == 'World':
                   res[d[0]][3] = d[1]-2866
                else:
                   res[d[0]][3] = d[1]
            else:
                res[d[0]] = [d[0], 0, 0, d[1]]
        result = [res[r] for r in res.keys()]
        cur.close()
        conn.close()
        return result[:3]
