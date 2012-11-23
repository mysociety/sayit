SayIt
=====

A project to upload and store audio and text of speeches.

Installation
------------

Something like the following, customised to your particular environment or set up:

    # Clone the repo
    mkdir sayit
    cd sayit
    git clone https://github.com/mysociety/sayit.git

    # Set up a python virtual environment, activate it
    virtualenv --no-site-packages virtualenv-sayit
    source virtualenv-sayit/bin/activate

    # Install required python packages
    cd sayit
    pip install --requirement requirements.txt

    cp conf/general.yml-example conf/general.yml
    # Alter conf/general.yml as per your set up

    # Set up database
    ./manage.py syncdb
    ./manage.py migrate

    # gather all the static files in one place
    ./manage.py collectstatic --noinput

Testing
-------

    ./manage.py test speeches

The Selenium tests currently uses Firefox, so make sure you have Firefox installed.

