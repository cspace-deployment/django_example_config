perl -ne 'print unless /\tOK\t/' $1 | cut -f1 | sort | uniq -c > counts.txt
perl -ne 'print unless /\tOK\t/' $1 > badterms.csv
for x in `cut -c6- counts.txt`; do
    grep "$x" badterms.csv | cut -f6,7,9 > $x.csv
done
wc -l *.csv
