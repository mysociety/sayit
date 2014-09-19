---
layout: page
title: Installation
---

Installation
============

You will need to have the following installed:

* [elasticsearch](http://elasticsearch.org/)

* [PostgreSQL](http://www.postgresql.org/) (it's possible it could work on
  another database that e.g. handles recursive SQL, but this would need work)

Installing SayIt as a Django app
--------------------------------

If you already have a Django project, and wish to use SayIt in it, you'll need
to do the following. This assumes you already know about installing packages in
Python with pip and hopefully in a virtualenv.

1. Add `django-sayit` (or e.g. `-e git+https://github.com/mysociety/sayit` if you
want the bleeding edge) to your requirements.txt file, or install directly with
pip:

        pip install django-sayit

1. Add the following entries to your `INSTALLED_APPS` list:

        'django.contrib.humanize',
        'haystack',
        'django_select2',
        'django_bleach',
        'easy_thumbnails',
        'popolo',
        'instances',
        'speeches',

1.  **Only if you're using South**  
    You will need to make sure `easy_thumbnails` is in your
    `SOUTH_MIGRATION_MODULES`, e.g.:

        SOUTH_MIGRATION_MODULES = {
            'easy_thumbnails': 'easy_thumbnails.south_migrations',
        }

    You will also need to install `popit-django` and add `popit` to
    `INSTALLED_APPS` as that is used by some of our older migrations.

1. Add the following line to your `MIDDLEWARE_CLASSES`:

        'speeches.middleware.InstanceMiddleware',

1. If you're not using it already, you'll need to set up haystack, with something
like:

        HAYSTACK_CONNECTIONS = {
            'default': {
                'ENGINE': 'haystack.backends.elasticsearch_backend.ElasticsearchSearchEngine',
                'URL': 'http://127.0.0.1:9200/',
                'INDEX_NAME': 'myproj',
            },
        }

1. Run syncdb (or migrate) to get the new SayIt models:

        ./manage.py syncdb

1. Add to your project `urls.py`:

        url(r'^speeches/', include('speeches.urls', namespace='sayit', app_name='speeches')),

### Optional configuration

* If you want to limit your speech output HTML to the same as the subset of Akoma
Ntoso we use for our import script, you'll want to have the following
[bleach](http://django-bleach.readthedocs.org/en/latest/) configuration:

        BLEACH_ALLOWED_TAGS = [
            'a', 'abbr', 'b', 'i', 'u', 'span', 'sub', 'sup', 'br',
            'p',
            'ol', 'ul', 'li',
            'table', 'caption', 'tr', 'th', 'td',
        ]

        BLEACH_ALLOWED_ATTRIBUTES = {
            '*': [ 'id', 'title' ], # class, style
            'a': [ 'href' ],
            'li': [ 'value' ],
        }

* You can optionally install `django-tastypie` to include its features.

Installing the example SayIt Django project
-------------------------------------------

You'll need to install pip and virtualenv (Debian/Ubuntu packages python-pip
and python-virtualenv).

1. Clone the repository:

        mkdir sayit
        cd sayit
        git clone https://github.com/mysociety/sayit.git

1. Create a postgres database and user:

        sudo -u postgres psql
        postgres=# CREATE USER sayit WITH password 'sayit';
        CREATE ROLE
        postgres=# CREATE DATABASE sayit WITH OWNER sayit;
        CREATE DATABASE

1. Set up a python virtual environment, and activate it:

        virtualenv --no-site-packages virtualenv-sayit
        source virtualenv-sayit/bin/activate

1. Install the required python packages:

        cd sayit
        pip install -e .

1.  Alter the settings to match your setup - the default example project looks
    for a PostgreSQL database with name sayit-example-project and a blank user.
    You can override settings by editing the existing files:

        vim example_project/settings/base.py

    or by creating a file at `example_project/settings/local.py` and putting
    your local configuration in there. `local.py` has access to the settings
    already set up and can change them, for example:

        echo "DATABASES['default']['USER'] = 'postgres'" >> local.py

1. Set up the database:

        ./manage.py syncdb

    This will ask you if you wish to create a Django superuser, which you'll
use to access the admin interface. You can always do it later with `./manage.py
createsuperuser`, but there's no harm in doing it now either, just remember the
details you choose!

1. The development server should now run fine:

        ./manage.py runserver

1. To gather all the static files together in deployment, you'll use, as normal:

        ./manage.py collectstatic --noinput
