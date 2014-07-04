from setuptools import setup, find_packages
import os
import sys

file_dir = os.path.abspath(os.path.dirname(__file__))

def read_file(filename):
    filepath = os.path.join(file_dir, filename)
    return open(filepath).read()

# Fix for Select2 py3 branching
if sys.version_info >= (3,):
    select2 = 'Django-Select2-Py3 >= 4.2.1, < 4.3'
else:
    select2 = 'Django-Select2 >= 4.2.2, < 4.3'

setup(
    name="django-sayit",
    version='1.1.0',
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
        'Django >= 1.4, < 1.7',
        select2,
        'django-qmethod == 0.0.3',
        'django-bleach >= 0.1.5',
        'audioread >= 1.0.1',
        'pyelasticsearch >= 0.6, < 0.7',
        'django-haystack >= 2.1, < 2.2',
        'mysociety-django-popolo >= 0.0.2',
        'mysociety-django-sluggable >= 0.2.5',
        'django-subdomain-instances >= 0.4',
    ],
    extras_require={
        'test': [
            'selenium',
            'mock',
            'django-nose == 1.2',
            'Mutagen',
        ],
        'develop': [
            'django-debug-toolbar',
            'python-dateutil < 2',
            'lxml',
            'South',
            'popit-django == 0.0.3',
        ],
        'scraping': [
            'beautifulsoup4',
            'requests_cache',
        ],
    },
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Framework :: Django',
        'License :: OSI Approved :: GNU Affero General Public License v3',
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Topic :: Database :: Front-Ends',
        'Topic :: Internet :: WWW/HTTP',
    ],
)
