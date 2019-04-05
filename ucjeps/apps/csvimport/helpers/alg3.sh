#set -e
set -x

# copy and unzip, rename file to .csv
rm -f Algae_csc_rev_20190403.*
cp ~/Downloads/Algae_csc_rev_20190403.txt.zip .
unzip Algae_csc_rev_20190403.txt.zip 
mv Algae_csc_rev_20190403.txt Algae_csc_rev_20190403.csv

perl -i -pe 's/recordedBy, associatedCollectors/associatedCollectors/' Algae_csc_rev_20190403.csv
perl -i -pe 's/habitat; substrate; associatedTaxa/habitat/' Algae_csc_rev_20190403.csv

# fix just a few geodeticDatum fields
# UC1840397 Sargassum sinicola (eliminating stray value)
perl -ne 'print if /\tQ\t/' Algae_csc_rev_20190403.csv
perl -i -pe 's/\tQ\t/\t\t/' Algae_csc_rev_20190403.csv 

# count values, then fix typos in georeferenceSource
perl -ne 'print if /\tWSG/' Algae_csc_rev_20190403.csv | wc -l
perl -ne 'print if /\tWGS84\t/' Algae_csc_rev_20190403.csv | wc -l

perl -i -pe 's/\tWSG *84\t/\tWGS84\t/' Algae_csc_rev_20190403.csv
perl -i -pe 's/\tWGS *84\t/\tWGS84\t/' Algae_csc_rev_20190403.csv

perl -ne 'print if /\tWGS84\t/' Algae_csc_rev_20190403.csv | wc -l
perl -ne 'print if /\tWSG84\t/' Algae_csc_rev_20190403.csv | wc -l

# recode geodeticDatum field
~/PycharmProjects/django_example_config/ucjeps/apps/csvimport/helpers/make-geolocate-changes.sh Algae_csc_rev_20190403.csv
# make changed to 'orgauthorities' (recordedBy and associatedCollectors)
~/PycharmProjects/django_example_config/ucjeps/apps/csvimport/helpers/make-org-changes.sh Algae_csc_rev_20190403.csv

# copy and rename file produce by scipts above
cp Algae_csc_rev_20190403.csv Algae_csc_rev_20190404_ogt-etc.csv 


