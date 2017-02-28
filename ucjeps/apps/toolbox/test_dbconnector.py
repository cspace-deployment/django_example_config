__author__ = 'Julian Jaffe'

import unittest
import time, sys
import dbqueries
from common import cspace
from os import path
from cspace_django_site import settings


class ConnectorTestCase(unittest.TestCase):
    def test_connection(self):
        self.assertEqual(dbqueries.testDB(dbqueries.cursor), "OK")

    def test_setQuery(self):
        config = cspace.getConfig(path.join(settings.BASE_PARENT_DIR, 'config'), "toolbox")
        institution = config.get('info','institution')
        qualifier = ''
        location = ''
        updateType = 'inventory'
        query = dbqueries.setquery('inventory', location, qualifier)
        self.assertEqual('SELECT' in query, True)

    def test_getlocations(self):
        elapsedtime = time.time()
        location = '1001'
        locations = dbqueries.getlocations(location, location, 3, 'bedlist')
        elapsedtime = time.time() - elapsedtime
        sys.stderr.write('all objects: %s :: %s\n' % (location, elapsedtime))
        # self.assertEqual(len(locations), 0)
        self.assertEqual(len(locations) > 0, True)


if __name__ == '__main__':
    unittest.main()
