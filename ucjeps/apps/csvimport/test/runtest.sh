PYTHON=python2.7
set -x
rm -f runlog.out
nohup time $PYTHON DWC2CSpace.py $1.csv ../config/csvimport.cfg ../config/DWC2CSpace-v2.csv ../config/collectionobject-v2.xml $1.valid.csv /dev/null /dev/null count > runlog.out 2>&1
grep -v Insec runlog.out > $1.count.log; rm runlog.out
nohup time $PYTHON DWC2CSpace.py $1.csv ../config/csvimport.cfg ../config/DWC2CSpace-v2.csv ../config/collectionobject-v2.xml $1.valid.csv $1.invalid.csv $1.terms.csv validate > runlog.out 2>&1
grep -v Insec runlog.out > $1.validate.log; rm runlog.out
nohup time $PYTHON DWC2CSpace.py $1.valid.csv ../config/csvimport.cfg ../config/DWC2CSpace-v2.csv ../config/collectionobject-v2.xml $1.upload.csv /dev/null /dev/null add > runlog.out 2>&1
grep -v Insec runlog.out > $1.add.log; rm runlog.out
#nohup ./reset.sh $1.upload.csv > $1.delete.log
