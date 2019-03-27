#!/bin/bash
cd $( dirname "${BASH_SOURCE[0]}" )
touch $1.inprogress.log
source set-config-ucjeps-dev.sh
if [ -e $1.add.csv ]; then
    # create a list of csids, then use the delete script to delete them
    cut -f2 $1.add.csv > csids.txt
    ./delete-multiple.sh collectionobjects csids.txt 
fi
rm $1.inprogress.log
rm csids.txt

