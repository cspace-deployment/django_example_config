
#    53	country
#    54	stateProvince
#    55	county

head -1 $1 | perl -pe 's/\t/\n/g' | nl

cut -f53 $1 | sort | uniq -c > country_before.txt
cut -f55 $1 | sort | uniq -c > county_before.txt

perl recodeColumns.pl 30countries.csv  $1     A1.csv 53
perl recodeColumns.pl 30counties.csv   A1.csv A2.csv 55

cut -f53 A2.csv | sort | uniq -c > country_after.txt
cut -f55 A2.csv | sort | uniq -c > county_after.txt

diff -y country_before.txt country_after.txt > country_diffs.txt
diff -y county_before.txt county_after.txt > county_diffs.txt


