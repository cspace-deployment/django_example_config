#!/bin/bash
cd $( dirname "${BASH_SOURCE[0]}" )
PYTHON=/var/www/venv/bin/python
DATE=$(date +%Y-%m-%d-%H-%M-%S)
set -x
touch $1.inprogress.log
for t in `ls $1.*`; do if echo "$t" | grep -q ".input."; then echo $t not removed; else rm $t ; fi ; done
rm $1.inprogress.log
