perl -i -pe 's/georef batch tool ....\-..\-..; GeoLocate/GEOLocate/' howell.csv 
perl -i -pe 's/georef batch tool ....\-..\-..\t/GEOLocate\t/' howell.csv 
perl -i -pe 's/GeoLocate; GeoLocate\t/GEOLocate\t/' howell.csv 
perl -i -pe 's/GeoLocate\t/GEOLocate\t/' howell.csv
