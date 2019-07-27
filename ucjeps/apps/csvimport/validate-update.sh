#!/bin/bash
cd $( dirname "${BASH_SOURCE[0]}" )
PYTHON=/var/www/venv/bin/python
set -x
touch $1.inprogress.log
rm -f $1.runlog.out
time $PYTHON DWC2CSpace.py $1.input.csv ../config/csvimport.cfg ../config/DWC2CSpace-v2.csv ../config/collectionobject-v2.xml $1.valid.csv $1.invalid.csv $1.terms.csv validate-update $2 > $1.runlog.out 2>&1
mv $1.valid.csv $1.update.csv
grep -v Insec $1.runlog.out > $1.validated.log; rm $1.runlog.out
cat $1.inprogress.log >> $1.runstatistics.log ; rm $1.inprogress.log