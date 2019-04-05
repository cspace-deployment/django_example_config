#set -e
set -x

cp $1 $1.old

head -1 $1 | perl -pe 's/\t/\n/g' | nl

# cut -f27 $1 | sort | uniq -c > recordedBy_before.txt
# cut -f28 $1 | sort | uniq -c > associatedCollectors_before.txt

#    53  country
#    54  stateProvince
#    55  county

perl recodeColumns.pl collectors.csv     $1        A1.csv 27
perl recodeColumns.pl determination.csv  A1.csv    A2.csv 28
perl recodeColumns.pl taxa.csv           A2.csv    A3.csv 14
perl recodeColumns.pl states.csv         A3.csv    A4.csv 54
perl recodeColumns.pl country.csv        A4.csv    A5.csv 53
perl recodeColumns.pl 4-counties-to-fix.csv A5.csv A6.csv 55

# cut -f27 A6.csv | sort | uniq -c > recordedBy_after.txt
# cut -f28 A6.csv | sort | uniq -c > associatedCollectors_after.txt

# diff -y recordedBy_before.txt recordedBy_after.txt > recordedBy_diffs.txt
# diff -y associatedCollectors_before.txt associatedCollectors_after.txt > associatedCollectors_diffs.txt

cp A6.csv $1

rm A?.csv

