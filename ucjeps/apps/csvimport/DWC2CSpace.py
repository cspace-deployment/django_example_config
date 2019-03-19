# -*- coding: utf-8 -*-
import csv
import sys

sys.path.append("../../ucjeps")

from common.unicode_hack import UnicodeReader, UnicodeWriter

from utils import load_mapping_file, validate_items, count_columns, getRecords, write_intermediate_files
from utils import send_to_cspace, count_stats, count_numbers, getConfig

CONFIGDIRECTORY = ''


def main():
    header = "*" * 100

    if len(sys.argv) < 8:
        print('%s <csv input file> <config file> <mapping file> <template> <output file> <terms file> <action>') % \
             sys.argv[0]
        sys.exit()

    print header
    print "DWC2CSPACE: input  file:       %s" % sys.argv[1]
    print "DWC2CSPACE: config file:       %s" % sys.argv[2]
    print "DWC2CSPACE: mapping file:      %s" % sys.argv[3]
    print "DWC2CSPACE: template:          %s" % sys.argv[4]
    print "DWC2CSPACE: validated file:    %s" % sys.argv[5]
    print "DWC2CSPACE: unvalidated file:  %s" % sys.argv[6]
    print "DWC2CSPACE: terms file:        %s" % sys.argv[7]
    print "DWC2CSPACE: action:            %s" % sys.argv[8]
    print header

    try:
        action = sys.argv[8]
        actions = 'count validate add update both'
        if not action in actions.split(' '):
            print 'DWC2CSPACE: Error! not a valid action: %s' % action
            sys.exit()
    except:
        print "DWC2CSPACE: action could not be understood: should be one of: %s" % actions
        sys.exit()

    try:
        with open(sys.argv[1], 'rb') as f:
            try:
                dataDict, inputRecords, lines, file_header = getRecords(f)
                print 'DWC2CSPACE: %s lines and %s records found in file %s' % (lines, len(inputRecords), sys.argv[1])
                print header
                if lines == -1:
                    print 'DWC2CSPACE: Error! %s' % inputRecords
                    sys.exit(1)
            except:
                print "DWC2CSPACE: could not get CSV records to load"
                sys.exit(1)
    except:
        print "DWC2CSPACE: could not open %s" % sys.argv[1]
        sys.exit(1)

    try:
        config = getConfig(sys.argv[2])
        print "DWC2CSPACE: hostname        %s" % config.get('connect', 'hostname')
        print "DWC2CSPACE: institution     %s" % config.get('info', 'institution')
        print header
    except:
        print "DWC2CSPACE: could not get cspace server configuration"
        sys.exit()

    try:
        print "DWC2CSPACE: loading mapping file %s\n" % sys.argv[3]
        mapping, errors, constants = load_mapping_file(sys.argv[3])
        print '\nDWC2CSPACE: %s valid records found in mapping file %s' % (len(mapping), sys.argv[3])
        # print mapping
        print header
        if errors != 0:
            print "DWC2CSPACE: terminating due to %s errors detected in mapping configuration" % errors
            sys.exit()
    except:
        print "DWC2CSPACE: could not get mapping configuration"
        sys.exit()

    try:
        with open(sys.argv[4], 'rb') as f:
            xmlTemplate = f.read()
            # print xmlTemplate
    except:
        print "DWC2CSPACE: could not get template %s" % sys.argv[4]
        sys.exit()

    try:
        outputfh = UnicodeWriter(open(sys.argv[5], 'wb'), delimiter="\t", quoting=csv.QUOTE_NONE, quotechar=chr(255))
    except:
        print "DWC2CSPACE: could not open validated file for write %s" % sys.argv[5]
        sys.exit()

    try:
        nonvalidfh = UnicodeWriter(open(sys.argv[6], 'wb'), delimiter="\t", quoting=csv.QUOTE_NONE, quotechar=chr(255))
    except:
        print "DWC2CSPACE: could not open nonvalidated file for write %s" % sys.argv[6]
        sys.exit()

    try:
        termsfh = UnicodeWriter(open(sys.argv[7], 'wb'), delimiter="\t", quoting=csv.QUOTE_NONE, quotechar=chr(255), escapechar='\\')
    except:
        print "DWC2CSPACE: could not open terms file for write %s" % sys.argv[5]
        sys.exit()

    successes = 0
    failures = 0

    if action == 'count':
        stats = count_columns(inputRecords, file_header)
        print '%-35s %10s %10s' % tuple(stats[1])
        print
        for s in stats[0]:
            print '%-35s %10s %10s' % tuple(s)
        print
        recordsprocessed = len(inputRecords)
        successes = len(inputRecords)

    elif action == 'validate':
        validated_data, nonvalidating_items, stats, number_check, keyrow = validate_items(mapping, constants, inputRecords, file_header, action)

        ok_count, bad_count, bad_values = count_stats(stats, mapping)

        if bad_count != 0:
            print "DWC2CSPACE: validation failed (%s fields had %s values in error)" % (bad_count, bad_values)
            # print "DWC2CSPACE: cowardly refusal to write invalid output file"
            # sys.exit(1)

        not_found, found, total = count_numbers(number_check)

        print "\n%s:  %s found, %s not found, %s total\n" % ('numbers', found, not_found, total)

        recordsprocessed, successes, failures = write_intermediate_files(stats, validated_data, nonvalidating_items, constants, file_header, mapping,
                                                                          outputfh, nonvalidfh, termsfh, number_check, keyrow)

    elif action in 'add update both'.split(' '):

        recordsprocessed, successes = send_to_cspace(action, inputRecords, file_header, xmlTemplate, outputfh)

    print "DWC2CSPACE: '%s records': %s processed, %s successful, %s failures" % (action, recordsprocessed, successes, failures)
    print header


if __name__ == "__main__":
    main()
