#set -e
set -x

FILE=temp_file.csv
HELPERS_DIR=~/PycharmProjects/django_example_config/ucjeps/apps/csvimport/helpers

# make a copy
cp $1 $FILE

perl -i -pe 's/recordedBy, associatedCollectors/associatedCollectors/' $FILE
perl -i -pe 's/habitat; substrate; associatedTaxa/habitat/' $FILE

# fix just a few geodeticDatum fields
# UC1840397 Sargassum sinicola (eliminating stray value)
perl -ne 'print if /\tQ\t/' $FILE
perl -i -pe 's/\tQ\t/\t\t/' $FILE

# fix one stray georeferenceProtocol value for UC790294
perl -i -pe 'if (/UC790294/) { s/\t10\tGeo/\t\tGeo/ } ' $FILE

# fix a few scientific names with weird characters in them
perl -i -p weird_names.pl $FILE

# count values, then fix typos in georeferenceSource, then check
perl -ne 'print if /\tWSG/' $FILE | wc -l
perl -ne 'print if /\tWGS84\t/' $FILE | wc -l

perl -i -pe 's/\tWSG *84\t/\tWGS84\t/' $FILE
perl -i -pe 's/\tWGS *84\t/\tWGS84\t/' $FILE

perl -ne 'print if /\tWGS84\t/' $FILE | wc -l
perl -ne 'print if /\tWSG84\t/' $FILE | wc -l

# recode geodeticDatum field
$HELPERS_DIR/make-geolocate-changes.sh $FILE
# make changed to 'orgauthorities' (recordedBy and associatedCollectors)

head -1 $FILE | perl -pe 's/\t/\n/g' | nl
echo

#    20  identifiedBy
#    27  recordedBy
#    28  associatedCollectors

#    53  country
#    54  stateProvince
#    55  county

cp $FILE A1.csv

# these are for identifiedBy
perl recodeColumns.pl determination.csv      A1.csv A2.csv 20; mv A2.csv A1.csv

# apply changes to both recordedBy and associatedCollectors
perl recodeColumns.pl collectors.csv         A1.csv A2.csv 27; mv A2.csv A1.csv
perl recodeColumns.pl collectors.csv         A1.csv A2.csv 28; mv A2.csv A1.csv

perl recodeColumns.pl taxa.csv               A1.csv A2.csv 14; mv A2.csv A1.csv

perl recodeColumns.pl states.csv             A1.csv A2.csv 54; mv A2.csv A1.csv
perl recodeColumns.pl country.csv            A1.csv A2.csv 53; mv A2.csv A1.csv

# this zaps the 1,200+ missing county values
#perl recodeColumns.pl county.csv             A1.csv A2.csv 55; mv A2.csv A1.csv

perl recodeColumns.pl sex.csv                A1.csv A2.csv 48; mv A2.csv A1.csv
#perl recodeColumns.pl 4-counties-to-fix.csv A1.csv A2.csv 55; mv A2.csv A1.csv

# duplicate the latlong columns: we need both verbatim and decimal versions
cut -f60,61 A1.csv > latlongs.csv
perl -i -pe 's/decimal/vdecimal/g' latlongs.csv
paste A1.csv latlongs.csv > $FILE

rm A?.csv latlongs.csv

echo "$FILE is the revised file"

