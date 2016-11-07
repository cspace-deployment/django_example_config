import sys, csv, uuid, operator

"""
Create "skeletal acquisition records" for BAMPFA

This has to be a repeatable process.

1. A ".tab" (delimited) file is extracted from FMPro.

2. Build an output file that has:

    a generated UUID (Acquisition CSID), IDNumberPart1, idnumberpart2,
    DateAcquired, Source, LegalStatus, StatusDate, CreditLine.

    This will be the source for skeletal acquisition records that we create.
    (If this is easy we might add some other fields.)

    For each unique combination of IDNumberPart1 and idnumberpart2,
        get the most frequently used values in the following five fields:
        DateAcquired, Source, LegalStatus, StatusDate, CreditLine

3. Generate a UUID for each unique combination of IDNumberPart1 and idnumberpart2 that
can persist as the acquisition CSID (with new UUIDs assigned as the job is rerun).
"""

"""
NB:
    IDnumber = 115
    IDNumberPart1 = 116
    idnumberpart2 = 117
    DateAcquired = 59
    Source = 238
    LegalStatus = 155
    StatusDate = 239
    CreditLine = 48
    For = 101
    HowAcquired = 114
"""

counts = {}
keys = {}
IDnumber = 115
columnsToCount = [59, 238, 155, 239, 48, 101, 114]

inputFile = sys.argv[1]
outputFile = sys.argv[2]

# inputFile = "/Users/jblowe/cinefilesAcq/collectionitems2.csv"
# outputFile = "testfile.csv"

FMProFile = csv.reader(open(inputFile, 'rb'), delimiter="\t", quotechar="\\")
collectionItems = {}
counts['Collection Items'] = 0
counts['Skeletal Acq Records output'] = 0


def CountMyDict(d, k, v, c):
    if k in d:
        pass
    else:
        d[k] = {}

    if v in d[k]:
        pass
    else:
        d[k][v] = {}

    if c in d[k][v]:
        d[k][v][c] += 1
    else:
        if c != '':
            d[k][v][c] = 1


for lineno, ci in enumerate(FMProFile):
    counts['Collection Items'] += 1
    ci = [x.strip() for x in ci]
    if len(ci) < 272:
        print "problem line %s" % lineno
        print ci
        continue
    key = '.'.join([ci[i] for i in [121, 116, 117]])
    if key[0] == '.': key = key[1:] # remove leading '.' if we made one...

    #print key + "\t",
    for var in columnsToCount:
        # print ci[var] + "\t",
        CountMyDict(collectionItems, key, var, ci[var])
        #print
    # make persistent csid (i.e. MD5 hash of (unique) IDnumber)
    # https://docs.python.org/2/library/uuid.html
    if not key in keys:
        csid = uuid.uuid3(uuid.NAMESPACE_DNS, key)
        CountMyDict(collectionItems, key, 999, csid)
    keys[key] = 1

outputfh = csv.writer(open(outputFile, 'wb'), delimiter="\t")

for key in collectionItems.keys():
    counts['Skeletal Acq Records output'] += 1
    vars = collectionItems[key]
    uuid = vars[999].keys()[0]
    outputRow = [str(uuid), key]
    for column in columnsToCount:
        columnValues = vars[column]
        sorted_values = sorted(columnValues.iteritems(), key=operator.itemgetter(1), reverse=True)
        if sorted_values == []: sorted_values = [['', '']]
        outputRow.append(sorted_values[0][0])

    outputfh.writerow(outputRow)

for s in counts.keys():
    print "%s: %s " % (s, counts[s])

