source set-config-ucjeps-dev.sh
cut -f2 $1 > csids.txt
~/PycharmProjects/Tools/devops/helpers/delete-multiple.sh collectionobjects csids.txt 
