#!/bin/bash
cd $( dirname "${BASH_SOURCE[0]}" )
PYTHON=/var/www/venv/bin/python
set -x
rm -f $1.$2.$3.out
touch $1.inprogress.log
time $PYTHON DWC2CSpace.py $1.input.csv ../config/csvimport.cfg ../config/fields.$3.csv ../config/template.$3.xml $1.$2.csv /dev/null /dev/null $2 $3 > $1.$2.$3.out 2>&1
cp $1.input.csv $1.$2.csv
grep -v $1.$2.$3.out > $1.counted.log
rm $1.$2.$3.out
rm $1.inprogress.log

