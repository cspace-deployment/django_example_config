#!/bin/bash
set -x
cd $( dirname "${BASH_SOURCE[0]}" )
rm -f $1.runlog.out
touch $1.inprogress.log
source set-config-ucjeps-dev.sh
if [ -e $1.*-audit.csv ]; then
    # create a list of csids, then use the delete script to delete them
    cut -f2 $1.*-audit.csv > csids.txt
    ./delete-multiple.sh $2 csids.txt > $1.runlog.out 2>&1
else
    echo $1.*-audit.csv not found. >> $1.runlog.out 2>&1
fi
mv $1.runlog.out $1.undone.log; rm $1.runlog.out
rm $1.inprogress.log
mv $1.added.log $1.archive.log
mv $1.updated.log $1.archive.log
rm csids.txt

