""""Some helper classes for writing scrapers.

These have been used to write scrapers from several sources for
sayit.mysociety.org including The Leveson Inquiry and the trial of Charles
Taylor.

WARNING: They're provided here in case they are useful to anyone writing
scrapers of their own, but should definitely not be considered part of a stable
API.

You'll need to install some extra dependencies if you want to use this module.
They're listed in requirements-scraping.txt and can be installed like this:

pip install -r requirements-scraping.txt
"""

import itertools
import os
import socket
import re

from exceptions import NotImplementedError, StandardError

from optparse import OptionParser

import bs4
import requests
import requests_cache
import subprocess

from instances.models import Instance
from speeches.models import Section, Speaker, Speech


def prevnext(it):
    prev, curr, next = itertools.tee(it, 3)
    prev = itertools.chain([None], prev)
    next = itertools.chain(itertools.islice(next, 1, None), [None])
    return itertools.izip(prev, curr, next)


class ScrapingError(StandardError):
    """Exception to represent all different sorts of scraping error."""


class BaseParser(object):
    name_fixes = {}

    # Subclasses should override instance to be the label of an appropriate
    # Instance object.
    instance = None

    def __init__(self, cache_dir=None):
        if not self.instance:
            raise StandardError(
                "Set the 'instance' class attribute to an appropriate label.")

        if cache_dir is None:
            raise StandardError(
                'Set cache_dir to the directory for the requests cache.')

        self.parser = OptionParser()
        self._add_parser_options()
        (self.options, self.args) = self.parser.parse_args()
        self._process_parser_options()

        self.instance = self.get_or_create(Instance, label=self.instance)
        self.cache_dir = os.path.join(cache_dir, self.instance.label)

        try:
            os.makedirs(self.cache_dir)
        except:
            pass

        self.requests = requests_cache.core.CachedSession(cache_dir)

    def _add_parser_options(self):
        self.parser.add_option(
            '--commit',
            dest='commit',
            help='commit to database',
            action='store_true',
            )
        self.parser.add_option(
            '--process-existing',
            dest='process_existing',
            help="Process files already downloaded (default is to skip)",
            action='store_true',
            )

    def _process_parser_options(self):
        self.commit = self.options.commit
        self.process_existing = self.options.process_existing

    def get_transcripts(self):
        """Returns an iterator of dictionaries representing single transcripts.

        Each dictionary should be in the form expected by parse_transcript.

        OVERRIDE IN SUBCLASS.
        """
        raise NotImplementedError

    def get_pdf(self, pdf_url, name=None):
        if not name:
            name = os.path.basename(pdf_url)

        file_pdf = os.path.join(self.cache_dir, name)
        file_text = file_pdf.replace('.pdf', '.txt')

        if os.path.exists(file_text):
            if not self.process_existing:
                return
        else:
            with self.requests.cache_disabled():
                try:
                    pdf_transcript = self.get_url(pdf_url, 'binary')
                except (requests.exceptions.HTTPError, socket.error):
                    raise ScrapingError('Error fetching {}'.format(pdf_url))

            with open(file_pdf, 'w') as fp:
                fp.write(pdf_transcript)

            subprocess.call(['pdftotext', '-layout', file_pdf])

        text = open(file_text).read()

        # Be sure to have ^L on its own line
        text = text.replace('\014', '\014\n')
        # Return an array of lines
        return re.split('\r?\n', text)

    def get_url(self, url, type='none'):
        resp = self.requests.get(url)
        resp.raise_for_status()
        if type == 'binary':
            return resp.content
        elif type == 'html':
            return bs4.BeautifulSoup(resp.text)
        return resp.text

    def run(self):
        for data in self.get_transcripts():
            self.parse(data)

    def skip_transcript(self, data):
        return False

    def top_section_heading(self, data):
        return 'Hearing, %s' % data['date'].strftime('%d %B %Y').lstrip('0')

    def get_parent_section(self, data):
        """Find the section to create the top section in.

        All speeches for this transcript will be created in a section with
        heading provided by top_section_heading.

        Override this method to put this section inside another section.
        """
        return None

    def parse_transcript(self, data):
        """Takes transcript and returns an iterator of Speech objects.

        Find all the speeches in the transcript represented by the dictionary
        data and return an iterator of them as Speech objects.

        OVERRIDE IN SUBCLASS.
        """
        raise NotImplementedError

    def parse(self, data):
        if self.skip_transcript(data):
            return

        date = data.get('date')
        top_section = self.get_or_create(
            Section, instance=self.instance, source_url=data['url'],
            heading=self.top_section_heading(data),
            parent=self.get_parent_section(data),
        )

        for speech in self.parse_transcript(data):
            if not speech:
                continue

            if speech.section:
                if speech.section.object:
                    section = speech.section.object
                else:
                    heading = self.prettify(speech.section.heading)
                    section = Section(
                        instance=self.instance,
                        heading=heading,
                        parent=top_section,
                        )
                    if self.commit:
                        section.save()
                    speech.section.object = section
            else:
                section = top_section
            if speech.speaker:
                speaker = self.prettify(speech.speaker)
                speaker = self.get_or_create(
                    Speaker, instance=self.instance, name=speaker)
            else:
                speaker = None

            if not speech.type:
                speech.type = ('speech'
                               if speaker or speech.speaker_display
                               else 'narrative')

            text = '</p>\n<p>'.join([' '.join(s) for s in speech.text])
            text = '<p>%s</p>' % text
            speech_date = speech.date or date
            speech = Speech(
                instance=self.instance,
                section=section,
                text=text,
                speaker=speaker,
                speaker_display=speech.speaker_display,
                type=speech.type,
                start_date=speech_date,
                start_time=speech.time,
            )
            if self.commit:
                speech.save()

    def fix_name(self, name):
        name = name.title().replace('.', '')
        name = re.sub(
            'Mc[a-z]',
            lambda mo: mo.group(0)[:-1] + mo.group(0)[-1].upper(),
            name)
        name = self.name_fixes.get(name, name)
        return name

    def prettify(self, s):
        return s

    # Special get_or_create that won't always commit
    def get_or_create(self, model, **attrs):
        try:
            obj = model.objects.get(**attrs)
        except model.DoesNotExist:
            obj = model(**attrs)
            if self.commit:
                obj.save()
        return obj


class ParserSection(object):
    object = None

    def __init__(self, heading):
        self.heading = heading


class ParserSpeech(object):
    # Some state variables
    current_date = None
    current_time = None
    current_section = None
    witness = None

    def __init__(self, speaker, text, speaker_display=None, typ=None):
        self.speaker = speaker
        self.speaker_display = speaker_display
        self.text = [[text]]
        self.type = typ
        self.date = self.current_date
        self.time = self.current_time
        self.section = self.current_section

    def add_para(self, text):
        self.text.append([text])

    def add_text(self, text):
        self.text[-1].append(text)

    @classmethod
    def reset(cls, morning):
        cls.current_date = None
        cls.current_time = None
        if morning:
            cls.current_section = None
            cls.witness = None
