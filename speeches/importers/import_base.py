import logging
import re

from popit.models import ApiInstance
from popit_resolver.resolve import SetupEntities, ResolvePopitName

from speeches.models import Speaker

logger = logging.getLogger(__name__)
name_rx = re.compile(r'^(\w+) (.*?)( \((\w+)\))?$')

class SpeechImportException (Exception):
    pass

class ImporterBase (object):

    def __init__(self, popit_url=None, instance=None, commit=True, **kwargs):
        self.instance = instance
        self.popit_url = popit_url
        self.commit = commit
        self.title = '(untitled)'

        if self.popit_url:
            self.ai, _ = ApiInstance.objects.get_or_create(url=self.popit_url)
        else:
            # XXX TODO This is not right.
            self.ai, _ = ApiInstance.objects.get_or_create(url='http://import.example.org/')

        self.person_cache = {}
        self.speakers_count = 0
        self.speakers_matched = 0
        self.speakers = {}

        self.resolver = None

    def init_popit_data(self):
        if self.popit_url:
            SetupEntities(self.popit_url).init_popit_data()

    def set_resolver_for_date(self, date_string='', date=None):
        if self.popit_url:
            self.resolver = ResolvePopitName(
                    date = date,
                    date_string = date_string)

    def make(self, cls, **kwargs):
        s = cls(instance=self.instance, **kwargs)
        if self.commit:
            s.save()
        elif s.title:
            logger.info(s.title)
        return s

    def get_person(self, name):
        cached = self.person_cache.get(name, None)
        if cached:
            return cached

        display_name = name or '(narrative)'

        speaker = None
        popit_person = None

        if name:
            self.speakers_count += 1
            if self.resolver:
                popit_person = self.resolver.get_person(display_name)

                if popit_person:
                    self.speakers_matched += 1
                    try:
                        speaker = Speaker.objects.get(
                            instance = self.instance,
                            person = popit_person)
                    except Speaker.DoesNotExist:
                        pass
                else:
                    logger.info(" - Failed to get user %s" % display_name)

        if not speaker:
            try:
                speaker = Speaker.objects.get(instance=self.instance, name=display_name)
            except Speaker.DoesNotExist:
                speaker = Speaker(instance=self.instance, name=display_name)
                if self.commit:
                    speaker.save()

            if popit_person:
                speaker.person = popit_person
                if self.commit:
                    speaker.save()

        self.person_cache[name] = speaker
        return speaker
