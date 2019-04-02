#!/bin/bash
cd $( dirname "${BASH_SOURCE[0]}" )
touch $2.inprogress.log
source set-config-ucjeps-dev.sh
if [ -e $2.add-audit.csv ]; then
    # create a list of csids, then use the delete script to delete them
    cut -f2 $2.add-audit.csv > csids.txt
    ./delete-multiple.sh $1 csids.txt 
else
    echo $2.add-audit.csv not found.
fi
rm $2.inprogress.log
rm csids.txt

