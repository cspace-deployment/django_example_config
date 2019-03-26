#!/bin/bash
cd $( dirname "${BASH_SOURCE[0]}" )
PYTHON=python2.7
set -x
touch $1.inprogress.log
rm -f runlog.out
nohup time $PYTHON DWC2CSpace.py $1.update.csv ../config/csvimport.cfg ../config/DWC2CSpace-v2.csv ../config/collectionobject-v2.xml $1.update.csv /dev/null /dev/null update > runlog.out 2>&1
grep -v Insec runlog.out > $1.updated.log; rm runlog.out
rm $1.inprogress.log

