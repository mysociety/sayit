---
layout: page
title: Installation
---

Installation
============

You will need to have the following installed:

* [elasticsearch](http://elasticsearch.org/)

* a database that handles recursive SQL – we've so far only tested it on
  PostgreSQL.

* The compass and zurb-foundation gems. Something like the following should
  install them, with the relevant gem bin directory then added to your `PATH`:

        gem install --user-install --no-document zurb-foundation compass

Installing SayIt as a Django app
--------------------------------

If you already have a Django project, and wish to use SayIt in it, you'll need
to do the following. This assumes you already know about installing packages in
Python with pip and hopefully in a virtualenv.

Add `django-sayit` (or e.g. `-e git+https://github.com/mysociety/sayit` if you
want it direct from version control) to your requirements.txt file, or install
directly with pip:

    pip install django-sayit

Add the following entries to your `INSTALLED_APPS` list (or at least the ones
that you're missing, hopefully you're e.g. already using South!):

    'django.contrib.humanize',
    'haystack',
    'south',
    'tastypie',
    'pagination',
    'pipeline',
    'django_select2',
    'django_bleach',
    'popit',
    'instances',
    'speeches',

Add the following line to your `MIDDLEWARE_CLASSES`:

    'speeches.middleware.InstanceMiddleware',

If you're not using it already, you'll need to set up haystack, with something
like:

    HAYSTACK_CONNECTIONS = {
        'default': {
            'ENGINE': 'haystack.backends.elasticsearch_backend.ElasticsearchSearchEngine',
            'URL': 'http://127.0.0.1:9200/',
            'INDEX_NAME': 'myproj',
        },
    }

The app uses [django-pipeline](http://django-pipeline.readthedocs.org/) for
JavaScript/CSS compilation. This can use a wide variety of compressors, but
let's use None for now:

    STATICFILES_STORAGE = 'pipeline.storage.PipelineCachedStorage'
    # You can use e.g. 'pipeline.compressors.yui.YUICompressor' in the two
    # lines below if you install YUI Compressor
    PIPELINE_CSS_COMPRESSOR = None
    PIPELINE_JS_COMPRESSOR = None

    PIPELINE_COMPILERS = (
        'pipeline_compass.compass.CompassCompiler',
    )
    PIPELINE_COMPASS_ARGUMENTS = '-r zurb-foundation'

    PIPELINE_CSS = {
        'sayit-default': {
            'source_filenames': (
                'speeches/sass/speeches.scss',
            ),
            'output_filename': 'css/speeches.css',
        },
    }

    PIPELINE_JS = {
        'sayit-default-head': {
            'source_filenames': (
                'speeches/js/jquery.js',
            ),
            'output_filename': 'js/sayit.head.min.js',
        },
        'sayit-default': {
            'source_filenames': (
                'speeches/js/foundation/foundation.js',
                'speeches/js/foundation/foundation.dropdown.js',
                'speeches/js/speeches.js',
            ),
            'output_filename': 'js/sayit.min.js',
        },
        'sayit-player': {
            'source_filenames': (
                'speeches/mediaelement/mediaelement-and-player.js',
            ),
            'output_filename': 'js/sayit.mediaplayer.min.js',
        },
        'sayit-upload': {
            'source_filenames': (
                'speeches/js/jQuery-File-Upload/js/vendor/jquery.ui.widget.js',
                'speeches/js/jQuery-File-Upload/js/jquery.iframe-transport.js',
                'speeches/js/jQuery-File-Upload/js/jquery.fileupload.js',
            ),
            'output_filename': 'js/sayit.upload.min.js',
        },
    }

If you want to limit your speech output HTML to the same as the subset of Akoma
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

Run the usual migrate to get the new SayIt models:

    ./manage.py migrate

Then add to your project `urls.py`:

    url(r'^speeches/', include('speeches.urls', namespace='sayit', app_name='speeches')),

Installing the example SayIt Django project
-------------------------------------------

You'll need to install pip, virtualenv and yui-compressor (Debian/Ubuntu
packages python-pip, python-virtualenv and yui-compressor).

Clone the repository:

    mkdir sayit
    cd sayit
    git clone https://github.com/mysociety/sayit.git

Create a postgres database and user:

    sudo -u postgres psql
    postgres=# CREATE USER sayit WITH password 'sayit';
    CREATE ROLE
    postgres=# CREATE DATABASE sayit WITH OWNER sayit;
    CREATE DATABASE

Set up a python virtual environment, and activate it:

    virtualenv --no-site-packages virtualenv-sayit
    source virtualenv-sayit/bin/activate

Install the required python packages:

    cd sayit
    pip install --requirement requirements.txt

Alter the settings to match your setup (the default example project looks for a
PostgreSQL database with name sayit-example-project and user postgres):

    vim example_project/settings/base.py

Set up the database:

    ./manage.py syncdb

(This will ask you if you wish to create a Django superuser, which you'll use to
access the admin interface. You can always do it later with `./manage.py
createsuperuser`, but there's no harm in doing it now either, just remember the
details you choose!)

    ./manage.py migrate

The development server should now run fine:

    ./manage.py runserver

To gather all the static files together in deployment, you'll use:

    ./manage.py collectstatic --noinput
