---
layout: page
title: Testing
---

Testing
=======

SayIt tests run on Travis with each commit and pull request, and you
can [see the output on Travis](https://travis-ci.org/mysociety/sayit).

To install the packages required to run the tests, run:

    pip install -e .[test]

(You will also need to make sure your system has [FFMPEG](https://www.ffmpeg.org/)
installed in order to avoid errors from tests which involve audio.)

Tests can be run with:

    ./manage.py test speeches

By default the Selenium-based tests are not run. These tests currently uses
Firefox, so make sure you have Firefox installed.

If you're on a headless server, eg: in a vagrant box, you'll need to install
the iceweasel and xvfb packages (see the commented out section of
`/conf/packages` for the packages you'll need to install).

After installing them, start Xvfb with:

    Xvfb :99 -ac &

And export your display variable:

    export DISPLAY=:99

You can then run the tests, including the Selenium ones, using:

    SELENIUM_TESTS=1 ./manage.py test

You might want to make that happen at every startup with the appropriates lines
in `/etc/rc.local` and `~/.bashrc`
