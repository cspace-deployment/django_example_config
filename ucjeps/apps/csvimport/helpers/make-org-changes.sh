head -1 $1 | perl -pe 's/\t/\n/g' | nl

cut -f27 $1 | sort | uniq -c > recordedBy_before.txt
cut -f28 $1 | sort | uniq -c > associatedCollectors_before.txt

perl recodeColumns.pl collectors.csv     $1 A1.csv 27
perl recodeColumns.pl determination.csv  A1.csv                A2.csv 28

cut -f27 A2.csv | sort | uniq -c > recordedBy_after.txt
cut -f28 A2.csv | sort | uniq -c > associatedCollectors_after.txt

diff -y recordedBy_before.txt recordedBy_after.txt > recordedBy_diffs.txt
diff -y associatedCollectors_before.txt associatedCollectors_after.txt > associatedCollectors_diffs.txt


