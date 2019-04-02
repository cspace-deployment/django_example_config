FILE=$1
perl -i -pe 's/georef batch tool ....\-..\-..; GeoLocate/GEOLocate/' $FILE
perl -i -pe 's/georef batch tool ....\-..\-..\t/GEOLocate\t/' $FILE
perl -i -pe 's/GeoLocate; GeoLocate\t/GEOLocate\t/' $FILE
perl -i -pe 's/GeoLocate\t/GEOLocate\t/' $FILE
perl -i -pe 's/\tte\t/\tGEOLocate\t/' $FILE