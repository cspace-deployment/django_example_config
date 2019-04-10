#!/bin/bash
cd $( dirname "${BASH_SOURCE[0]}" )
PYTHON=python2.7
set -x
rm -f $1.runlog.out
grep -v Insec $1.runlog.out > $1.validate.log; rm $1.runlog.out
touch $1.inprogress.log
time $PYTHON DWC2CSpace.py $1.input.csv ../config/csvimport.cfg ../config/fields.collectors.csv ../config/template.collectors.xml $1.add-audit.csv /dev/null /dev/null add $2 > $1.runlog.out 2>&1
grep -v Insec $1.runlog.out > $1.added.log; rm $1.runlog.out
rm $1.inprogress.log
