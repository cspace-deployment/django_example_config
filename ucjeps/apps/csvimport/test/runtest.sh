set -x
rm -f nohup.out
nohup time python DWC2CSpace.py $1.csv ../config/csvimport.cfg ../config/DWC2CSpace-v2.csv ../config/collectionobject-v2.xml $1.results.csv /dev/null count 
grep -v Insec nohup.out > $1.count.log; rm nohup.out
nohup time python DWC2CSpace.py $1.csv ../config/csvimport.cfg ../config/DWC2CSpace-v2.csv ../config/collectionobject-v2.xml $1.results.csv $1.terms.csv validate 
grep -v Insec nohup.out > $1.validate.log; rm nohup.out
nohup time python DWC2CSpace.py $1.results.csv ../config/csvimport.cfg ../config/DWC2CSpace-v2.csv ../config/collectionobject-v2.xml $1.upload.csv /dev/null add 
grep -v Insec nohup.out > $1.add.log; rm nohup.out
#nohup ./reset.sh $1.upload.csv > $1.delete.log
