#### A description of a method for managing updates to CSpace using a large delimited file

_Not the only way to do this!_

UCJEPS has a largish delimited file (80,000+ rows by 50+ columns) that needs to be
added to CollectionSpace

The following is a brief description of how on the RTL side
we handled the informal "pipeline" of changes to bring this file
into accord with what was in the UCJEPS CSpace database, so that
it could be imported using the new csvImport facility.

The steps are basically as follows:

1. Accept the "latest and greatest" version of the file from UCJEPS.
1. Apply known changes to the input data (e.g. Country, State, Country values; Collector names, etc.)
1. "Queue" (i.e. upload) the file using the csvImport webapp.
1. Process the file there: 
    1.  check format ("count")
    1.  verify content of cells ("validate"")
1. Rinse and repeat as needed until data file and database are in sync.
1. Add the validated set of records to CSpace using csvImport.

The activities involved are:

1. Adding batches of terms (Collector Names, Geographic terms) to CSpace.
1. Adding individual terms via the UI (mostly this is done by UCJEPS staff).
1. Updating columns in the input file on the basis of 2-column "before-and-after" files.
1. Tweaking individual column values, via one-liners, etc.
1. Uploading and processing files via the csvImport webapp.

Below are descriptions of how one might accomplish some of these steps:

##### Add new collectors to Default org authority:

```
cd ~/django_example_config/
git pull -v
cp ucjeps/config/DWC2CSpace-v2.csv ~/ucjeps/config/DWC2CSpace-v2.csv 
cp ucjeps/config/*collectors*  ~/ucjeps/config/
# check configuration for this step
less ~/ucjeps/config/fields.collectors.csv
less ~/ucjeps/config/template.collectors.xml
```

Run the script to add these Collector names to CSpace:

```
nohup ./add-authority.sh /home/app_webapps/csvimport/ucjeps/associatedCollectors orgauthorities/6d89bda7-867a-4b97-b22f/items 2>&1 &
```

##### Change a column in an input file using before-and-after values:

* Download the "invalid" records for the run.
* Chop off the first column
* Make a before-and-after file with the appropriate values (in this case, using the "not found" terms in the validation run)
* Recode the desired colum values.

```
# not shown: download via csvImport webapp the terms and invalid records.

# make the before and after file
perl -ne 'print unless /\tOK\t/' Algae_csc_rev_20190408-oagts-etc.terms.csv | grep -v associatedCollectors | cut -f6,7,8 > associatedCollectors.csv
# edit column 2 with the "after" values
vi associatedCollectors.csv 

# make the "invalid" file into a new input file, with the recoded values
mv Algae_20190411_revised-oagtsc-etc.invalid.csv Algae_20190412_associatedcollectors.input.csv
# trim off the first column: it is the csid of the record in cspace, if it was found
cut -f2- Algae_20190412_associatedcollectors.input.csv > foo
mv foo Algae_20190412_associatedcollectors.input.csv 
# recode the values
perl recodeColumns.pl associatedCollectors.csv Algae_20190412_associatedcollectors.input.csv A2.csv 28

change:      associatedCollectors.csv
input:       Algae_20190412_associatedcollectors.input.csv
output:      A2.csv
change col:  28

rewrite pairs read:    691
vacuous pairs skipped: 0
lines read:            1450
lines output:          1450
changed lines:         1193
unchanged lines:       257

mv A2.csv Algae_20190412_associatedcollectors.input.csv
```

You now have a fine input file with the corrected values; upload and process this file with csvImport.
