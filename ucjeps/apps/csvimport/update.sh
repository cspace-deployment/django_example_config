#!/bin/bash
cd $( dirname "${BASH_SOURCE[0]}" )
PYTHON=python2.7
set -x
touch $1.inprogress.log
rm -f $1.runlog.out
time $PYTHON DWC2CSpace.py $1.update.csv ../config/csvimport.cfg ../config/DWC2CSpace-v2.csv ../config/collectionobject-v2.xml $1.update-audit.csv /dev/null /dev/null update $2 > $1.runlog.out 2>&1
grep -v Insec $1.runlog.out > $1.updated.log; rm $1.runlog.out
cat $1.inprogress.log >> $1.runstatistics.log ; rm $1.inprogress.log

