grep -v https Algae_Mar-20-2019-jbl.terms.csv > a1
perl -ne 'print unless /\tOK\t/' a1 > a2
cut -f1 a2 | sort | uniq -c
grep county a2 | cut -f6,7 | sort > microalgae.county.csv
grep recordedBy a2 | cut -f6,7 | sort > microalgae.recordedBy.csv
grep country a2 | cut -f6,7 | sort > microalgae.country.csv
wc -l *.csv
cut -f67 ~/csvimport/ucjeps/Algae_Mar-20-2019-jbl.input.csv | sort | uniq -c
cut -f53-57 Algae_Mar-28-2019-fix2.input.csv | expand -30 | grep "Viet" | less


sort -rn -k2 -t$'\t' microalgae.county.csv | head -30
sort -rn -k2 -t$'\t' microalgae.country.csv | head -30
sort -rn -k2 -t$'\t' microalgae.recordedBy.csv | head -30

rm a1 a2 
