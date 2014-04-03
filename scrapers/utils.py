import itertools
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
os.environ['DJANGO_SETTINGS_MODULE'] = 'spoke.settings'

from optparse import OptionParser
import re

import bs4
import requests_cache
import subprocess

from instances.models import Instance
from speeches.models import Section, Speaker, Speech

BASE_DIR = os.path.dirname(__file__)

def prevnext(it):
    prev, curr, next = itertools.tee(it, 3)
    prev = itertools.chain([None], prev)
    next = itertools.chain(itertools.islice(next, 1, None), [None])
    return itertools.izip(prev, curr, next)

class BaseParser(object):
    name_fixes = {}

    def __init__(self):
        parser = OptionParser()
        parser.add_option('--commit', dest='commit', help='commit to database', action='store_true')
        (options, args) = parser.parse_args()
        self.commit = options.commit

        self.requests = requests_cache.core.CachedSession(os.path.join(BASE_DIR, 'data', self.instance))
        self.instance = self.get_or_create(Instance, label=self.instance)

    def get_pdf(self, pdf_url, name=None):
        cache_dir = self.instance.label
        if not name:
            name = os.path.basename(pdf_url)

        dir_pdf = os.path.join(BASE_DIR, 'data', cache_dir)
        try:
            os.makedirs(dir_pdf)
        except:
            pass
        file_pdf = os.path.join(dir_pdf, name)
        file_text = file_pdf.replace('.pdf', '.txt')
        if not os.path.exists(file_text):
            pdf_transcript = self.get_url(pdf_url, 'binary')
            fp = open(file_pdf, 'w')
            fp.write(pdf_transcript)
            fp.close()
            subprocess.call([ 'pdftotext', '-layout', file_pdf ])
        text = open(file_text).read()

        # Be sure to have ^L on its own line
        text = text.replace('\014', '\014\n')
        # Return an array of lines
        return re.split('\r?\n', text)

    def get_url(self, url, type='none'):
        resp = self.requests.get(url)
        if resp.status_code != 200:
            raise Exception
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

    def top_section_title(self, data):
        return 'Hearing, %s' % data['date'].strftime('%d %B %Y').lstrip('0')

    def parse(self, data):
        if self.skip_transcript(data):
            return

        date = data.get('date')
        top_section = self.get_or_create(Section, instance=self.instance, title=self.top_section_title(data))

        for speech in self.parse_transcript(data):
            if not speech: continue
            if speech.section:
                if speech.section.object:
                    section = speech.section.object
                else:
                    title = self.prettify(speech.section.title)
                    section = Section(instance=self.instance, title=title, parent=top_section)
                    if self.commit:
                        section.save()
                    speech.section.object = section
            else:
                section = top_section
            if speech.speaker:
                speaker = self.prettify(speech.speaker)
                speaker = self.get_or_create(Speaker, instance=self.instance, name=speaker)
            else:
                speaker = None
            text = '</p>\n<p>'.join([ ' '.join(s) for s in speech.text ])
            text = '<p>%s</p>' % text
            speech_date = speech.date or date
            speech = Speech(
                instance=self.instance, section=section, text=text,
                speaker=speaker, speaker_display=speech.speaker_display,
                start_date=speech_date, start_time=speech.time
            )
            if self.commit:
                speech.save()

    def fix_name(self, name):
        name = name.title().replace('.', '')
        name = re.sub('Mc[a-z]', lambda mo: mo.group(0)[:-1] + mo.group(0)[-1].upper(), name)
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
    def __init__(self, title):
        self.title = title

class ParserSpeech(object):
    # Some state variables
    current_date = None
    current_time = None
    current_section = None
    witness = None

    def __init__(self, speaker, text, speaker_display=None):
        self.speaker = speaker
        self.speaker_display = speaker_display
        self.text = [ [ text ] ]
        self.date = self.current_date
        self.time = self.current_time
        self.section = self.current_section

    def add_para(self, text):
        self.text.append([ text ])

    def add_text(self, text):
        self.text[-1].append(text)

    @classmethod
    def reset(cls, morning):
        cls.current_date = None
        cls.current_time = None
        if morning:
            cls.current_section = None
            cls.witness = None
