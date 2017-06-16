from setuptools import setup, find_packages
import os
import sys

file_dir = os.path.abspath(os.path.dirname(__file__))


def read_file(filename):
    filepath = os.path.join(file_dir, filename)
    return open(filepath).read()


# Fix for dateutil/SSL py3 support
if sys.version_info >= (3,):
    dateutil = 'python-dateutil >= 2'
    ssl = []
else:
    dateutil = 'python-dateutil < 2'
    # @see https://github.com/kennethreitz/requests/blob/master/requests/packages/urllib3/contrib/pyopenssl.py
    ssl = [
        'pyOpenSSL >= 0.14',
        'ndg-httpsclient >= 0.3.2',
        'pyasn1 >= 0.1.7',
    ]

if os.environ.get('TOX'):
    django = 'Django >= 1.8.5'
else:
    django = 'Django >= 1.8.5, < 2.0'

setup(
    name="django-sayit",
    version='1.5',
    description='A data store for speeches and transcripts to make them searchable and pretty.',
    long_description=read_file('README.rst'),
    author='mySociety',
    author_email='sayit@mysociety.org',
    url='https://github.com/mysociety/sayit',
    packages=find_packages(exclude=('example_project', 'example_project.*')),
    include_package_data=True,
    install_requires=[
        'psycopg2 >= 2.5.1, < 2.6',
        'pytz >= 2013d',
        'six >= 1.4.1',
        django,
        'mysociety-Django-Select2 == 4.3.2.1',
        'audioread >= 1.0.1',
        'elasticsearch >= 0.4',
        'django-haystack >= 2.5, < 2.6',
        'django-bleach >= 0.2.1',
        'mysociety-django-popolo >= 0.0.5',
        'mysociety-django-sluggable >= 0.2.7',
        'django-subdomain-instances >= 2.0',
        'easy-thumbnails >= 2.4.1',
        'unicode-slugify == 0.1.1',
    ] + ssl,
    extras_require={
        'test': [
            'selenium >= 3',
            'mock',
            'django-nose == 1.4.4',
            'Mutagen',
            'lxml',
            dateutil,
            'requests_cache',
        ],
        'develop': [
            'flake8',
            'django-debug-toolbar',
        ],
        'scraping': [
            'beautifulsoup4',
        ],
    },
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Framework :: Django',
        'License :: OSI Approved :: GNU Affero General Public License v3',
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'Topic :: Database :: Front-Ends',
        'Topic :: Internet :: WWW/HTTP',
    ],
)
