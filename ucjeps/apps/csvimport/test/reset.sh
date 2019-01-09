source ~/PyCharmProjects/Tools.keep/devops/helpers/set-config-ucjeps-dev.sh
cut -f2 $1 > csids.txt
~/PyCharmProjects/Tools/devops/helpers/delete-multiple.sh collectionobjects csids.txt 
