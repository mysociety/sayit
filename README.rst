SayIt
=====

SayIt is an open source Django application or project to store transcripts
and present them in a modern, searchable format.

One example of SayIt in action is mySociety's website
`sayit.mysociety.org <http://sayit.mysociety.org>`_ which contains a variety
of transcripts, including:

* `The Leveson Inquiry <http://leveson.sayit.mysociety.org>`_
* `The Charles Taylor trial <http://charles-taylor.sayit.mysociety.org>`_
* `The plays of Shakespeare <http://shakespeare.sayit.mysociety.org>`_

Another is `OpenHouse Nova Scotia <http://www.openhousens.ca>`_, providing an
unofficial record of the proceedings of the Nova Scotia House of Assembly.

SayIt is a `Poplus component <http://poplus.org>`_
by `mySociety <http://www.mysociety.org/>`_.

Get involved
------------

If you have transcripts you'd like to be included on our website, or have
the technical skills to create such transcripts, please see
http://sayit.mysociety.org/about/community.

For more information on how to use SayIt in your own Django project or as a
standalone site, please see our
`documentation <http://mysociety.github.io/sayit/>`_:

* `Installation <http://mysociety.github.io/sayit/install/>`_
* `Testing <http://mysociety.github.io/sayit/testing/>`_
* `Development <http://mysociety.github.io/sayit/develop/>`_

Testing
-------

In a virtualenv, to run the tests::

    pip install -e .[test]
    ./manage.py test speeches

.. image:: https://travis-ci.org/mysociety/sayit.png?branch=master
   :alt: Build Status
   :target: https://travis-ci.org/mysociety/sayit
