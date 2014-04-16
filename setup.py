from setuptools import setup, find_packages
import os

file_dir = os.path.abspath(os.path.dirname(__file__))

def read_file(filename):
    filepath = os.path.join(file_dir, filename)
    return open(filepath).read()

def install_requires():
    reqs = read_file('requirements.txt')
    reqs = reqs.splitlines()
    reqs = [ x for x in reqs if x and x[0] != '#' and x[0:2] != '-e' ]
    return reqs

setup(
    name="django-sayit",
    version='1.0.0',
    description='A data store for speeches and transcripts to make them searchable and pretty.',
    long_description=read_file('README.rst'),
    author='mySociety',
    author_email='sayit@mysociety.org',
    url='https://github.com/mysociety/sayit',
    packages=find_packages(exclude=('example_project', 'example_project.*')),
    include_package_data=True,
    install_requires=install_requires(),
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
