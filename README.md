This Directory contains _sample_ configuration files for the various UCB tenants using the "Django webapps".

It also contains the code for custom apps for UCB tenants (i.e. apps that are not contributed to the core set, or were written specifically for a tenant).

Most of the config files will work with _production_ UCB deployments unmodified, but for use on Dev (or other) deployments
hostname, port, and other changes need to be made.

(For local development, you should make your own versions of most of these config files, and that they get copied to the appropriate directories after you have `configured` and `deployed` the apps using `setup.sh`.)

The files for the various UCB deployments here are designed to be deployed using
the "setup.sh" script in the cspace_django_project directory.  That script
merges the files here with the "vanilla" Django framework ("`cspace_django_project`" )to create a
working Django project directory with suitable customizations.

As a generalization, the following files need to be present in the tenant directory for `setup.sh` to work properly.

* apps directory, containing the source code for any custom apps.
* config directory, containing the .cfg, .csv and other files required for each app.
* fixtures directory, containing any fixture content that needs to be deployed.
* project_app.py, a module containing the INSTALLED_APPS dictionary Django requires.
* projedct_urls.py, a module to be used as top-level urls.py for the project.

If you follow this pattern for your own custom apps and webapp configuration, you'll be able to use 
setup.sh as well, which may ease your maintenance and deployment efforts.

== Deploying the UCB webapps

On any development machine (laptop, vm, etc), clone both Django-related git repositories:

```
git clone git@github.com:cspace-deployment/django_example_config.git
git clone git@github.com:cspace-deployment/cspace_django_project.git
```

To create the git tags for these repos

* move to the parent directory of both cloned repos
* from the parent dir of the repos, run the /devops/make-django-release.pl script

```
./make-django-release.pl djconf-5.0 django_example_config.git "a few fixes and enhancements”
./make-django-release.pl cdp-5.0 cspace_django_project "a few more fixes and enhancements”
```

NB: the tag prefixes (e.g. ```cdp-5.0``) must already exist. To make new major and minor
"releases" you'll need to make and commit the new start tag yourself.

To deploy the tagged sources

* Login to the server targeted for the release
* Switch users to the “app_webapps”

```
ssh cspace-dev-02.ist.berkeley.edu
sudo su - app_webapps
#move into the cspace_django_project folder
cd cspace_django_project
#from the cspace_django_project folder:

# if you have not already configured the apps (i.e. if this is an initial install)
# you will need to
# note that the WSGI configuration for Apache needs to be set up as well.
# Follow the instructions in the README in the cspace_django_project directory
# for initial setup.

# However, once that's done, you need only issue the following command to get
# an existing deployment updated:
./setup.sh deploy ${webapp}

# e.g., ./setup deploy ucjeps
```

Then, normally, you should restart Apache

At the moment, ’setup.sh’ script deploys the tip of the master branch.
Someday, it should take an additional parameter, which is the tag to deploy.

Good hunting!

