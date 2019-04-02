#!/bin/bash
cd $( dirname "${BASH_SOURCE[0]}" )
PYTHON=python2.7
set -x
touch $1.inprogress.log
rm -f runlog.out
nohup time $PYTHON DWC2CSpace.py $1.input.csv ../config/csvimport.cfg ../config/DWC2CSpace-v2.csv ../config/collectionobject-v2.xml $1.valid.csv $1.invalid.csv $1.terms.csv validate $2 > runlog.out 2>&1
mv $1.valid.csv $1.update.csv
grep -v Insec runlog.out > $1.validated.log; rm runlog.out
rm $1.inprogress.log
