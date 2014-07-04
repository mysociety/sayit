---
layout: page
title: Developement
---

Development
===========

To install packages used in development, such as the Django debug toolbar and
things needed for Akoma Ntoso import, run:

    pip install -e .[develop]

CSS
---

The CSS is written using SASS, Compass, and Foundation. In order to compile the
CSS, you will need to install the compass and zurb-foundation gems. The
following should install them, with the relevant gem bin directory then added
to your `PATH`:

    gem install --user-install --no-document zurb-foundation compass

A git pre-commit hook is provided in `conf/hook-pre-commit` to automatically
compile the CSS whenever you commit altered SCSS. Start using that with (in the
project root):

    ln -s ../../conf/hook-pre-commit .git/hooks/pre-commit

Manually you can use something like:

    compass compile \
        --output-style=compressed \
        -r zurb-foundation \
        --sass-dir speeches/static/speeches/sass \
        --css-dir speeches/static/speeches/css \
        speeches/static/speeches/sass/speeches.scss

Or:

    compass watch \
        --output-style=compressed \
        -r zurb-foundation \
        --sass-dir speeches/static/speeches/sass \
        --css-dir speeches/static/speeches/css

Model changes
-------------

South migration files are included in the code. If you wish to change the
database model, be sure to use South to add new migrations. As explained in the
install documentation, you will need to install `popit-django` and add `popit`
to `INSTALLED_APPS` for the migrations to run.

If you have already run `syncdb` for SayIt, and then start using South, you
will need to fake the migrations up to the point you synced.
