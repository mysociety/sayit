---
layout: page
title: Welcome
---

Welcome to SayIt
================

SayIt is a Django application designed to radically reduce the effort of
putting transcripts online in an attractive, searchable, linkable, readable
way.

This site is about how to install your own copy of SayIt on your own server,
and how to import data into it. [mySociety] (the UK charity that wrote this
code) runs a public installation of SayIt for hosting transcripts that you
might be interested in. For more information, please see
[sayit.mysociety.org].

Technical Overview
------------------

The `speeches` directory contains a standard [Django] app, and the
`example_project` directory contains a sample basic Django project that uses
SayIt. You may also be interested in the project that is [sayit.mysociety.org],
which can be found [on GitHub](https://github.com/mysociety/sayit.mysociety.org).

SayIt has been installed on Debian squeeze and wheezy. If Django and PostgreSQL
run on it, it should theoretically be okay; do let us know of any problems.

Installation
------------

SayIt can be installed as a Django app, or as a standalone server. For full
details, see the [installation documentation](install/).

[mySociety]: http://www.mysociety.org/
[Django]: http://www.djangproject.com/
[sayit.mysociety.org]: http://sayit.mysociety.org/
