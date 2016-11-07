# global variables

from os import path
from common import cspace # we use the config file reading function
from cspace_django_site import settings

config = cspace.getConfig(path.join(settings.BASE_PARENT_DIR, 'config'), 'eloan')

MAXMARKERS = int(config.get('eloan', 'MAXMARKERS'))
MAXRESULTS = int(config.get('eloan', 'MAXRESULTS'))
MAXLONGRESULTS = int(config.get('eloan', 'MAXLONGRESULTS'))
MAXFACETS = int(config.get('eloan', 'MAXFACETS'))
IMAGESERVER = config.get('eloan', 'IMAGESERVER')
BMAPPERSERVER = config.get('eloan', 'BMAPPERSERVER')
BMAPPERDIR = config.get('eloan', 'BMAPPERDIR')
BMAPPERCONFIGFILE = config.get('eloan', 'BMAPPERCONFIGFILE')
SOLRSERVER = config.get('eloan', 'SOLRSERVER')
SOLRCORE = config.get('eloan', 'SOLRCORE')
SOLRQUERYPARAM = config.get('eloan', 'SOLRQUERYPARAM')
LOCALDIR = config.get('eloan', 'LOCALDIR')
DROPDOWNS = config.get('eloan', 'DROPDOWNS').split(',')
SEARCH_QUALIFIERS = config.get('eloan', 'SEARCH_QUALIFIERS').split(',')


PARMS = {
    # this first one is special
    'keyword': ['Keyword', 'true', 'a keyword search value, please', 'text', ''],

    # the rest are mapping the solr field names to django form labels and fields
    'csid': ['id', 'true', '', 'id', ''],
    'accession': ['Specimen ID', 'true', '', 'accessionnumber_txt', ''],
    'determination': ['Determination', 'true', '', 'determination_txt', ''],
    'majorgroup': ['Major Group', 'true', '', 'majorgroup_txt', ''],
    'collector': ['Collector', 'true', '', 'collector_txt', ''],
    'collectorverbatim': ['Collector', 'true', '', 'collectorverbatim_s', ''],
    'collectionnumber': ['Collection Number', 'true', '', 'collectornumber_txt', ''],
    'collectiondate': ['Collection Date', 'true', '', 'collectiondate_txt', ''],
    'earlycollectiondate': ['earlycollectiondate_dt', 'true', '', 'earlycollectiondate_dt', ''],
    'latecollectiondate': ['latecollectiondate', 'true', '', 'latecollectiondate_txt', ''],
    'locality': ['Locality', 'true', '', 'locality_txt', ''],
    'county': ['County', 'true', '', 'collcounty_txt', ''],
    'state': ['State', 'true', '', 'collstate_txt', ''],
    'country': ['Country', 'true', '', 'collcountry_txt', ''],
    'elevation': ['Elevation', 'true', '', 'elevation_txt', ''],
    'minelevation': ['Min elevation', 'true', '', 'minelevation_f', ''],
    'maxelevation': ['Max elevation', 'true', '', 'maxelevation_f', ''],
    'elevationunit': ['Elevation unit', 'true', '', 'elevationunit_txt', ''],
    'habitat': ['Habitat', 'true', '', 'habitat_txt', ''],
    'L1': ['L1', 'true', '', 'location_0_coordinate', ''],
    'L2': ['L2', 'true', '', 'location_1_coordinate', ''],
    'trscoordinates': ['TRS coordinates', 'true', '', 'trscoordinates_txt', ''],
    'datum': ['Datum', 'true', '', 'datum_txt', ''],
    'coordinatesource': ['Coordinate source', 'true', '', 'coordinatesource_txt', ''],
    'coordinateuncertainty': ['Coordinate uncertainty', 'true', '', 'coordinateuncertainty_f', ''],
    'coordinateuncertaintyunit': ['Coordinate uncertainty unit', 'true', '', 'coordinateuncertaintyunit_txt', ''],
    'updatedat': ['Last updated at', 'true', '', 'updatedat_dt', ''],
    'previousdeterminations': ['Previous Determinations', 'true', '', 'previousdeterminations_ss', ''],
    'localname': ['Local Name', 'true', '', 'localname_txt', ''],
    'briefdescription': ['Description', 'true', '', 'briefdescription_txt', ''],
    'associatedtaxa': ['Associated Taxa', 'true', '', 'associatedtaxa_ss', ''],
    'typeassertions': ['Type Assertions', 'true', '', 'typeassertions_ss', ''],
    'othernumbers': ['Other Numbers', 'true', '', 'othernumbers_ss', ''],
    'labelheader': ['Label Header', 'true', '', 'labelheader_txt', ''],
    'labelfooter': ['Label Footer', 'true', '', 'labelfooter_txt', ''],
    'depth': ['Depth', 'true', '', 'depth_txt', ''],
    'mindepth': ['Min. Depth', 'true', '', 'mindepth_txt', ''],
    'maxdepth': ['Max. Depth', 'true', '', 'maxdepth_txt', ''],
    'depthunit': ['Depth Unit', 'true', '', 'depthunit_txt', ''],
    'sex': ['Sex', 'true', '', 'sex_s', ''],
    'phase': ['Phase', 'true', '', 'phase_s', ''],
    'determinationdetails': ['Determination Details', 'true', '', 'determinationdetails_txt', ''],
    'blobs': ['blob_ss', 'true', '', 'blob_ss', ''],
}
