SayIt
=====

A project to upload and store audio and text of speeches.

Documentation
-------------
Documentation (a work in progress) can be found at: http://mysociety.github.com/sayit/

Installation
------------

Something like the following, customised to your particular environment or set up:

    # Clone the repo
    mkdir sayit
    cd sayit
    git clone https://github.com/mysociety/sayit.git

    cd sayit

    # Install the required software packages
    Assuming you're on a debian/ubuntu server:
    grep -v '#' conf/packages | sudo xargs apt-get install -y

    # Create a postgres database and user
    sudo -u postgres psql
    postgres=# CREATE USER sayit WITH password 'sayit';
    CREATE ROLE
    postgres=# CREATE DATABASE sayit WITH OWNER sayit;
    CREATE DATABASE

    # Set up a python virtual environment, activate it
    # this assumes that you will set up the virtualenv in .. 
    # (e.g. outside the repo.  
    #  You can use ~/.virtualenvs/ etc. if you prefer)
    virtualenv --no-site-packages ../virtualenv-sayit
    source ../virtualenv-sayit/bin/activate

    # Install required python packages
    pip install --requirement requirements.txt

    cp conf/general.yml-example conf/general.yml
    # Alter conf/general.yml as per your set up
    #    use the 'sayit' account as above for SAYIT_DB_{USER,NAME,PASS}
    # 
    # For *development* use only:
    #    use recommendations for BASE_{HOST,PORT}
    #    you don't need Google Analytics
    #    for AT&T API details, you can use these 2 dummy values
    #        ATT_OAUTH_URL: 'http://att.oauth.url.example.org/'
    #        ATT_API_URL: 'http://att.api.url.example.org/'
    #    DJANGO_SECRET_KEY isn't needed

    # Set up database
    ./manage.py syncdb

    # This will ask you if you wish to create a Django superuser, which you'll
    # use to access the sayit admin interface. You can always do it later with
    # ./manage.py createsuperuser, but there's no harm in doing it now either,
    # just remember the details you choose!

    ./manage.py migrate

    # gather all the static files in one place
    ./manage.py collectstatic --noinput

Testing
-------

    ./manage.py test speeches

The Selenium tests currently uses Firefox, so make sure you have Firefox installed.

If you're on a headless server, eg: in a vagrant box, you'll need to install the
iceweasel and xvfb packages (see the commented out section of /conf/packages)

After installing them, start Xvfb with:

    Xvfb :99 -ac &

And export your display variable:

    export DISPLAY=:99

You might want to make that happen at every startup with the appropriates lines in
`/etc/rc.local` and `~/.bashrc`

Using the API
-------------

1) Tastypie API is read-only

TODO

2) Speech upload API

  * Get the login token from `/instance/token` for the instance you want to
  connect to

  * `curl -c cookie.jar -d login-token='[[TOKEN]]' http://[[site]]/accounts/mobile-login/`

For the curl login request, do not target the wildcarded domain (e.g. for the
instance), as the token is already linked to the instance

  * `curl -v -b cookie.jar -F "audio=@path/to/audio.mp3;type=audio/mpeg" -F timestamps='[{"timestamp":0},{"timestamp":30000}]' http://[[instance]].[[site]]/api/v0.1/recording/`

Note that timestamps are in milliseconds, so 30000 above is 30 seconds.  The
JSON structure for the list of timestamps can also include the speaker ID, for
example `{"timestamp":0,"speaker",1}`.

It may be easier to test with short audio snippets until you are able to
successfully upload.
