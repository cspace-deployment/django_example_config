#!/bin/bash
cd $( dirname "${BASH_SOURCE[0]}" )
PYTHON=python2.7
set -x
touch $1.inprogress.log
rm -f $1.runlog.out
time $PYTHON DWC2CSpace.py $1.input.csv ../config/csvimport.cfg ../config/DWC2CSpace-v2.csv ../config/collectionobject-v2.xml $1.valid.csv $1.invalid.csv $1.terms.csv validate $2 > $1.runlog.out 2>&1
mv $1.valid.csv $1.both.csv
grep -v Insec $1.runlog.out > $1.validated.log; rm $1.runlog.out
rm $1.inprogress.log
