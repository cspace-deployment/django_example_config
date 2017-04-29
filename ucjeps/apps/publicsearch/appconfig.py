# global variables

from os import path
from common import cspace # we use the config file reading function
from cspace_django_site import settings

config = cspace.getConfig(path.join(settings.BASE_PARENT_DIR, 'config'), 'publicsearch')

MAXMARKERS = int(config.get('search', 'MAXMARKERS'))
MAXRESULTS = int(config.get('search', 'MAXRESULTS'))
MAXLONGRESULTS = int(config.get('search', 'MAXLONGRESULTS'))
MAXFACETS = int(config.get('search', 'MAXFACETS'))
IMAGESERVER = config.get('search', 'IMAGESERVER')
BMAPPERSERVER = config.get('search', 'BMAPPERSERVER')
BMAPPERDIR = config.get('search', 'BMAPPERDIR')
BMAPPERCONFIGFILE = config.get('search', 'BMAPPERCONFIGFILE')
BMAPPERURL = config.get('search', 'BMAPPERURL')
SOLRSERVER = config.get('search', 'SOLRSERVER')
SOLRCORE = config.get('search', 'SOLRCORE')
LOCALDIR = config.get('search', 'LOCALDIR')
DROPDOWNS = config.get('search', 'DROPDOWNS').split(',')
SEARCH_QUALIFIERS = config.get('search', 'SEARCH_QUALIFIERS').split(',')
TITLE = config.get('search', 'TITLE')

# still need to move this into a config file.
# could be the same one as above, or a different one.
PARMS = {
    # this first one is special
    'keyword': ['Keyword', 'true', 'a keyword search value, please', 'text', ''],

    # the rest are mapping the solr field names to django form labels and fields
    'csid': ['csid', 'true', '', 'csid_s', ''],
    'accession': ['Specimen ID', 'true', '', 'accessionnumber_s', ''],
    'determination': ['Determination', 'true', '', 'determination_txt', ''],
    'termformatteddisplayname': ['Determination', 'true', '', 'termformatteddisplayname_s', ''],
    'majorgroup': ['Major Group', 'true', '', 'majorgroup_txt', ''],
    'family': ['Family', 'true', '', 'family_txt', ''],
    'collector': ['Collector(s)', 'true', '', 'collector_txt', 'ss'],
    'collectorverbatim': ['Collector(s) (verbatim)', 'true', '', 'collectorverbatim_s', ''],
    'collectionnumber': ['Collection Number', 'true', '', 'collectornumber_txt', ''],
    'collectiondate': ['Collection Date', 'true', '', 'collectiondate_txt', ''],
    'earlycollectiondate': ['earlycollectiondate_dt', 'true', '', 'earlycollectiondate_dt', ''],
    'latecollectiondate': ['latecollectiondate', 'true', '', 'latecollectiondate_txt', ''],
    'locality': ['Locality', 'true', '', 'locality_txt', ''],
    'otherlocalities': ['Other Localities', 'true', '', 'otherlocalities_ss', 'ss'],
    'alllocalities': ['All Localities', 'true', '', 'alllocalities_txt', 'ss'],
    'localitynote': ['Locality Note', 'true', '', 'localitynote_txt', ''],
    'localitysource': ['Locality Source', 'true', '', 'localitysource_txt', ''],
    'localitysourcedetail': ['Locality Source Detail', 'true', '', 'localitysourcedetail_txt', ''],
    'county': ['County', 'true', '', 'collcounty_s', ''],
    'state': ['State', 'true', '', 'collstate_s', ''],
    'country': ['Country', 'true', '', 'collcountry_s', ''],
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
    'previousdeterminations': ['Previous Determinations', 'true', '', 'previousdeterminations_txt', 'ss'],
    'localname': ['Local Name', 'true', '', 'localname_txt', ''],
    'briefdescription': ['Description', 'true', '', 'briefdescription_txt', ''],
    'associatedtaxa': ['Associated Taxa', 'true', '', 'associatedtaxa_txt', 'ss'],
    'typeassertions': ['Type Assertions', 'true', '', 'typeassertions_txt', 'ss'],
    'othernumber': ['Other Numbers', 'true', '', 'othernumber_txt', 'ss'],
    'ucbgaccessionnumber': ['UCBG Accession Number', 'true', '', 'ucbgaccessionnumber_txt', ''],
    'loanstatus': ['Loan Status', 'true', '', 'loanstatus_txt', ''],
    'loannumber': ['Loan Number', 'true', '', 'loannumber_txt', ''],
    'labelheader': ['Label Header', 'true', '', 'labelheader_txt', ''],
    'labelfooter': ['Label Footer', 'true', '', 'labelfooter_txt', ''],
    'depth': ['Depth', 'true', '', 'depth_txt', ''],
    'mindepth': ['Min. Depth', 'true', '', 'mindepth_txt', ''],
    'maxdepth': ['Max. Depth', 'true', '', 'maxdepth_txt', ''],
    'depthunit': ['Depth Unit', 'true', '', 'depthunit_txt', ''],
    'cultivated': ['Cultivated', 'true', '', 'cultivated_s', ''],
    'sex': ['Sex', 'true', '', 'sex_txt', ''],
    'phase': ['Phase', 'true', '', 'phase_txt', ''],
    'sheets': ['Sheets', 'true', '', 'sheet_s', ''],
    'determinationdetails': ['Determination Details', 'true', '', 'determinationdetails_txt', ''],
    'determinationqualifier': ['Determination Qualifier', 'true', '', 'determinationqualifier_s', ''],
    'comments': ['Comments', 'true', '', 'comments_ss', 'ss'],
    'blobs': ['blob_ss', 'true', '', 'blob_ss', ''],
}
