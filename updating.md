---
layout: page
title: Updating your code
---

# Updating your code

<p class="lead">Keeping your code up to date means you get new features and bug
fixes implemented by other users of the component.</p>

## Updating SayIt used as a Django app

These instructions are the same as for any Django app you are using that you
would want to update.

1. The first step depends upon how are you dealing with dependencies in your
project. A couple of common options include the following:

    1. Update the version you have pinned in your project's `requirements.txt`
    and run `pip install -r requirements.txt`;
    1. Run `pip install --upgrade django-sayit`

    This will update SayIt, plus any changes to its dependencies.

1. `migrate` if you're using South, or have Django 1.7+ with built in
migrations, to get any changes to the database models.

1. `collectstatic` to collect new/changed static files for deployment.

## Updating SayIt with its example Django project

1. `git fetch` and `git merge` from the git repo (either the mySociety one or
your own fork of it), dealing with any of your own local changes how you wish
(if you think they would be useful to others, please do submit them as pull
requests).

1. Follow from step 2 above.
