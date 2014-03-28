import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
os.environ['DJANGO_SETTINGS_MODULE'] = 'spoke.settings'

from optparse import OptionParser

from instances.models import Instance
from speeches.models import Section, Speaker, Speech

class BaseParser(object):
    def __init__(self):
        parser = OptionParser()
        parser.add_option('--commit', dest='commit', help='commit to database', action='store_true')
        (options, args) = parser.parse_args()
        self.commit = options.commit

        self.instance = self.get_or_create(Instance, label=self.instance)

    def run(self):
        for data in self.get_transcripts():
            self.parse(data)

    def skip_transcript(self, data):
        return False

    def parse(self, data):
        if self.skip_transcript(data):
            return

        date = data.get('date')
        date_section = self.get_or_create(Section, instance=self.instance, title='Hearing, %s' % date.strftime('%d %B %Y').lstrip('0'))  

        for speech in self.parse_transcript(data):
            if not speech: continue
            if speech.section:
                if speech.section.object:
                    section = speech.section.object
                else:
                    title = self.prettify(speech.section.title)
                    section = Section(instance=self.instance, title=title, parent=date_section)
                    if self.commit:
                        section.save()
                    speech.section.object = section
            else:
                section = date_section
            if speech.speaker:
                speaker = self.prettify(speech.speaker)
                speaker = self.get_or_create(Speaker, instance=self.instance, name=speaker)
            else:
                speaker = None
            text = '</p>\n<p>'.join([ ' '.join(s) for s in speech.text ])
            text = '<p>%s</p>' % text
            speech = Speech(instance=self.instance, section=section, text=text, speaker=speaker, start_date=date, start_time=speech.time)
            if self.commit:
                speech.save()

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
    current_time = None
    current_section = None
    witness = None

    def __init__(self, speaker, text):
        self.speaker = speaker
        self.text = [ [ text ] ]
        self.time = self.current_time
        self.section = self.current_section

    def add_para(self, text):
        self.text.append([ text ])

    def add_text(self, text):
        self.text[-1].append(text)

    @classmethod
    def reset(cls, morning):
        cls.current_time = None
        if morning:
            cls.current_section = None
            cls.witness = None
