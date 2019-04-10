#!/bin/bash
cd $( dirname "${BASH_SOURCE[0]}" )
PYTHON=python2.7
set -x
touch $1.inprogress.log
rm -f $1.runlog.out
time $PYTHON DWC2CSpace.py $1.both.csv ../config/csvimport.cfg ../config/DWC2CSpace-v2.csv ../config/collectionobject-v2.xml $1.both-audit.csv /dev/null /dev/null both $2 > $1.runlog.out 2>&1
grep -v Insec $1.runlog.out > $1.updated.log; rm $1.runlog.out
rm $1.inprogress.log
