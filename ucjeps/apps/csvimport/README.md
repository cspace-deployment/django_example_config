## CSV Import

A tool to import delimited files (commas, tabs) into CSpace


How to deploy

1. Set up the webapp the usual way (i.e. follow the instructions for
deploying Django webapps)
1. Make the following directories to how the various job files:

```
cd
mkdir -p csvimport/ucjeps
mkdir -p csvimport/pahma
chcon -R -t httpd_sys_content_t csvimport/
```

3. The "static vocabularies" need to be made available. This is done by
fetching the JSON configuration file using the CSpace UI and placing it
in the config directory:

Download the UI configuration from https://ucjeps.cspace.berkeley.edu/config.
(Click the 'Save configuration as JSON" link to download.)

Then you'll have to get it up to the server somehow:

```
scp cspace-ui-config.json cspace-prod-01.ist.berkeley.edu:/tmp/cspace-ui-config-ucjeps.json
```

Note the filename; it is hardcoded in the csvImport program right now!

```
cp /tmp/cspace-ui-config-ucjeps.json ~/ucjeps/config
```

#### The command line interface (CLI)

You can also run csvImport from the command line, without using the
webapp. There's not a good motivation for doing that that I can think of
but for long jobs or many batches of files it might be useful.

Here's how to set up and run the code. Note that if csvImport is already installed
you may consider simply running it where it is installed.

Otherwise:


1. Clone the two repos you'll need.

```
git clone git@github.com:cspace-deployment/django_example_config.git
git clone git@github.com:cspace-deployment/cspace_django_project.git
```

2. Set things up (NB: this is not the "full" setup for Django webapps, just enough
   to get the CLI version of csvimport working.

```
cd cspace_django_project
cp -r ../django_example_config/ucjeps/apps/csvimport .
cp ../django_example_config/ucjeps/config/* ../config
# you may (or may not) have to install some Python dependencies
pip install -r requirements.txt
```

3. Three configuration files are needed. Probably you'll only need to edit `csvimport.cfg`,

```
../config/csvimport.cfg
../config/DWC2CSpace-v2.csv
../config/collectionobject-v2.xml
```

NB: make sure the hostname in `csvimport` is the one you intend! Dev or Prod!
    And that the credentials are valid!

```
vi ../config/csvimport.cfg
```

4. Count, Validate, Add, Update...

You'll need to point to your input file. You can try one of the test files provided:

Count:

```
nohup time python DWC2CSpace.py test_1_commas_unicode.csv ../config/csvimport.cfg ../config/DWC2CSpace-v2.csv ../config/collectionobject-v2.xml test_1_commas_unicode.results.csv /dev/null count >test_1_commas_unicode.counts.log

```


Validate:

```
nohup time python DWC2CSpace.py test_1_commas_unicode.csv ../config/csvimport.cfg ../config/DWC2CSpace-v2.csv ../config/collectionobject-v2.xml test_1_commas_unicode.results.csv test_1_commas_unicode.terms.csv validate

```

Add:

```
nohup time python DWC2CSpace.py test_1_commas_unicode.results.csv ../config/csvimport.cfg ../config/DWC2CSpace-v2.csv ../config/collectionobject-v2.xml test_1_commas_unicode.upload.csv /dev/null add

```


Erase what you just uploaded:

```
nohup ./reset.sh test_1_commas_unicode.upload.csv > test_1_commas_unicode.delete.log
```