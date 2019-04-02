#!/bin/bash
cd $( dirname "${BASH_SOURCE[0]}" )
PYTHON=python2.7
set -x
rm -f runlog.out
touch $1.inprogress.log
nohup time $PYTHON DWC2CSpace.py $1.input.csv ../config/csvimport.cfg ../config/DWC2CSpace-v2.csv ../config/collectionobject-v2.xml $1.count.csv /dev/null /dev/null count $2 > runlog.out 2>&1
cp $1.input.csv $1.count.csv
grep -v Insec runlog.out > $1.counted.log; rm runlog.out
rm $1.inprogress.log

