import calendar
from datetime import datetime
import logging
import os, sys
import pickle
import re, string

from lxml import etree
from lxml import objectify

from django.db import models
from django.utils import timezone
from django.conf import settings

from popit.models import Person, ApiInstance
from speeches.models import Section, Speech, Speaker
from popit_resolver.resolve import SetupEntities, ResolvePopitName
from django.core.exceptions import ImproperlyConfigured

logger = logging.getLogger(__name__)
name_rx = re.compile(r'^(\w+) (.*?)( \((\w+)\))?$')

class SpeechImportException (Exception):
    pass

class ImporterBase (object):

    def __init__(self, instance=None, commit=True, ai = None, **kwargs):
        self.instance = instance
        self.commit = commit
        self.start_date = None
        self.title = '(untitled)'
        self.popit_url = settings.POPIT_API_URL

        if not self.popit_url:
            raise ImproperlyConfigured("POPIT_API_URL was not set")

        # TODO get this url from the AN document, or from config/parameter
        if ai:
            self.ai = ai
        else:
            self.ai, _ = ApiInstance.objects.get_or_create(url=self.popit_url)
        self.use_cache = True

        self.person_cache = {}
        self.speakers_count   = 0
        self.speakers_matched = 0
        self.speakers     = {}

        self.resolver = None

    def init_popit_data(self):
        SetupEntities(self.popit_url).init_popit_data()

    def set_resolver_for_date(self, date_string='', date=None):
        self.resolver = ResolvePopitName(
                date = date,
                date_string = date_string)

    def make(self, cls, **kwargs):
        args = kwargs
        if cls == Speech:
            args['title'] = args.get('title', self.title)
            args['start_date'] = self.start_date

        s = cls(instance=self.instance, **args)
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
            speaker, _ = Speaker.objects.get_or_create(
                instance = self.instance, 
                name = display_name)

            if popit_person:
                speaker.person = popit_person
                speaker.save()

        self.person_cache[name] = speaker
        return speaker
