This Directory contains *sample* configuration files for the various django projects.

Most of the files will work with production deployments unmodified, but for use on Dev
hostname, port, and other changes need to be made.

The files for the various UCB deployments here are designed to be deployed using
the "setup.sh" script in the cspace_django_project directory.  That script
merges the files here with the "vanilla" Django framework to create a
Django project directory with suitable customizations.

As a generalization, the following files need to be present for each tenant:

* apps directory, containing the source code for any custom apps.
* config directory, containing the .cfg, .csv and other files required for each app.
* fixtures directory, containing any fixture content that needs to be deployed.
* project_app.py, a module containing the INSTALLED_APPS dictionary Django requires.
* projedct_urls.py, a module to be used as top-level urls.py for the project.

