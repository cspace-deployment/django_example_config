head -1 Algae_Feb-20-2019.csv | perl -pe 's/\t/\n/g' | nl

cut -f27 Algae_Feb-20-2019.csv | sort | uniq -c > recordedBy_before.txt
cut -f28 Algae_Feb-20-2019.csv | sort | uniq -c > associatedCollectors_before.txt

perl recodeColumns.pl collectors.csv     Algae_Feb-20-2019.csv A1.csv 27
perl recodeColumns.pl determination.csv  A1.csv                A2.csv 28

cut -f27 A2.csv | sort | uniq -c > recordedBy_after.txt
cut -f28 A2.csv | sort | uniq -c > associatedCollectors_after.txt

diff -y recordedBy_before.txt recordedBy_after.txt > recordedBy_diffs.txt
diff -y associatedCollectors_before.txt associatedCollectors_after.txt > associatedCollectors_diffs.txt


