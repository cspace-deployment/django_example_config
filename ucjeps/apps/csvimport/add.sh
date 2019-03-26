#!/bin/bash
cd $( dirname "${BASH_SOURCE[0]}" )
PYTHON=python2.7
set -x
rm -f runlog.out
grep -v Insec runlog.out > $1.validate.log; rm runlog.out
touch $1.inprogress.log
nohup time $PYTHON DWC2CSpace.py $1.add.csv ../config/csvimport.cfg ../config/DWC2CSpace-v2.csv ../config/collectionobject-v2.xml $1.add.csv /dev/null /dev/null add > runlog.out 2>&1
grep -v Insec runlog.out > $1.added.log; rm runlog.out
rm $1.inprogress.log
