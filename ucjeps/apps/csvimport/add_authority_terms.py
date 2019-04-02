import requests
import os
import re
import time
import sys, csv
from Counter import Counter

from copy import deepcopy
from xml.etree.ElementTree import tostring, parse, Element, fromstring
from xml.sax.saxutils import escape

from unicode_hack import UnicodeReader, UnicodeWriter


def createXMLpayload(template, values, institution):
    payload = deepcopy(template)
    for v in values.keys():
        payload = payload.replace('{' + v + '}', escape(values[v]))
    # get rid of remaining unsubstituted template variables
    payload = re.sub('(<.*?>){(.*)}(<.*>)', r'\1\3', payload)
    return payload


start = time.time()
delim = '\t'

print (len(sys.argv))

CREDENTIALS = sys.argv[1]
BASE_URL = sys.argv[2]
# e.g. BASE_URL = 'https://bampfa.cspace.berkeley.edu/cspace-services/personauthorities/1e3308ba-9d64-49e7-9541
INPUT_FILE = sys.argv[3]

PAGE_OPT = '?pgSz=1'

failed_gets = 0
failed_puts = 0
successful_calls = 0

headers = {'Content-Type': 'application/xml; charset=UTF-8'}

initial_get = BASE_URL + '/items' + PAGE_OPT
r = requests.get(initial_get, auth=tuple(CREDENTIALS.split(':')))

if (r.status_code < 200 or r.status_code > 300):
    print ('The request {0} could not be fulfilled. Please try again.'.format(initial_get))

try:
    xml = fromstring(r.content)
    csids = xml.findall('.//csid')
    for i in csids:
        pass
except:
    raise


with open(sys.argv[2], 'w') as f2:
    writer = UnicodeWriter(f2, delimiter=delim, quoting=csv.QUOTE_NONE, quotechar=chr(255))
    with open(INPUT_FILE, 'r') as f1:
        reader = UnicodeReader(f1, delimiter=delim, quoting=csv.QUOTE_NONE, quotechar=chr(255))
        for lineno, row in enumerate(reader):
            if lineno == 0:
                header = row
                writer.writerow(row)
                for col in header:
                    pass
                column_count = len(header)
            else:
                for i, cell in enumerate(row):
                    if cell != '':
                        types[header[i]][cell] += 1
                writer.writerow(row)

for c in range(len(csids)):
    csid = re.findall('>(\S+?)<', csids[c])[0]

    request = BASE_URL + csid
    print ("Processing {0}".format(request))

    get_response = requests.get(request, auth=(user, password))
    if (get_response.status_code < 200 and get_response.status_code >= 300):
        print("The item with CSID {0} failed to be fetched".format(csid))
        failed_reqs_file.write(
            "The item with CSID {0} failed to be fetched with status code {1} because {2}".format(csid,
                                                                                                  get_response.status_code,
                                                                                                  get_response.content))
        failed_gets += 1
        continue

    content = get_response.content

    put_request = requests.put(request, content, auth=(user, password), headers=headers)
    if (put_request.status_code < 200 and put_request.status_code >= 300):
        print("The item with CSID {0} failed to be PUTted".format(csid))
        failed_reqs_file.write(
            "The item with CSID {0} failed to be PUTted with status code {1} because {2}".format(csid,
                                                                                                 put_request.status_code,
                                                                                                 put_request.content))
        failed_puts += 1
        continue

    successful_calls += 1
    success_file.write("The item with CSID {0} was successfully updated. \n".format(csid))

end = time.time()
print("Time elapsed: {0} seconds".format(str(end - start)))
