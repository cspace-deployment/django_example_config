#!/bin/bash
cd $( dirname "${BASH_SOURCE[0]}" )
PYTHON=/var/www/venv/bin/python
set -x
rm -f $1.runlog.out
grep -v Insec $1.runlog.out > $1.validate.log; rm $1.runlog.out
touch $1.inprogress.log
time $PYTHON DWC2CSpace.py $1.add.csv ../config/csvimport.cfg ../config/DWC2CSpace-v2.csv ../config/collectionobject-v2.xml $1.add-audit.csv /dev/null /dev/null add $2 > $1.runlog.out 2>&1
grep -v Insec $1.runlog.out > $1.added.log; rm $1.runlog.out
cat $1.inprogress.log >> $1.runstatistics.log ; rm $1.inprogress.log
