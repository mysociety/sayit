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

from popit.models import Person, ApiInstance
from speeches.models import Section, Speech, Speaker

logger = logging.getLogger(__name__)
name_rx = re.compile(r'^(\w+) (.*?)( \((\w+)\))?$')

class SpeechImportException (Exception):
    pass

class ImportAkomaNtoso (object):

    def __init__(self, instance=None, commit=True):
        self.instance = instance
        self.commit = commit
        self.start_date = None
        self.title = '(untitled)'

        # TODO get this url from the AN document, or from config/parameter
        popit_url = 'http://sa-test.matthew.popit.dev.mysociety.org/api/v0.1/'
        self.ai, _ = ApiInstance.objects.get_or_create(url=popit_url)
        self.use_cache = True

        self.person_cache = {}
        self.speakers_count   = 0
        self.speakers_matched = 0

    def init_popit_data(self, date_string):
        # TODO this should be in popit-django.  Will try to structure things so that this
        # code can be reused there if possible!

        def add_url(collection, api_client):
            collection_url = api_client._store['base_url']
            for doc in collection:
                doc['popit_url'] = collection_url + '/' + doc['id']
            return collection

        # Stringy comparison is sufficient here
        def date_valid(collection, api_client):
            def _date_valid(doc):
                if doc['start_date']:
                    if start_date > date_string:
                        return False
                if doc['end_date']:
                    if end_date < date_string:
                        return False
                return True

            return filter(_date_valid, collection)

        persons = self.get_collection('persons', add_url)
        organizations = self.get_collection('organizations')
        memberships = self.get_collection('memberships')

        for m in memberships.values():
            person = persons[m['person_id']]
            person.setdefault('memberships', [])
            person['memberships'].append(m)

            organization = organizations[m['organization_id']]
            organization.setdefault('memberships', [])
            organization['memberships'].append(m)

        self.persons = persons
        self.organizations = organizations
        self.memberships = memberships
        self.already_spoken = []

    def get_collection(self, collection, fn=None):

        pickle_path = '.' # TODO, where is sanest place to put this?
        pickle_file = os.path.join(pickle_path, '%s.pickle' % collection)

        if self.use_cache:
            try:
                collection = pickle.load( open(pickle_file, 'r') )
                return collection
            except:
                pass

        api_client = self.ai.api_client(collection)
        objects = api_client.get()['result']
        if fn:
            objects = fn(objects, api_client)

        objects = dict([ (doc['id'], doc) for doc in objects ])

        pickle.dump(objects, open(pickle_file, 'w'), -1)

        return objects

    def import_xml(self, document_path):
        #try:
        tree = objectify.parse(document_path)
        xml = tree.getroot()

        debateBody = xml.debate.debateBody
        mainSection = debateBody.debateSection 

        self.title = '%s (%s)' % (
                mainSection.heading.text, 
                etree.tostring(xml.debate.preface.p, method='text'))

        section = self.make(Section, title=self.title)

        #try:
        start_date = xml.debate.preface.p.docDate.get('date')
        self.init_popit_data(start_date)

        self.start_date = datetime.strptime(start_date, '%Y-%m-%d')

        #except Exception as e:
            #raise e
            # pass

        self.visit(mainSection, section)

        return section

        #except Exception as e:
            #raise e
            # raise SpeechImportException(str(e))

    def make(self, cls, **kwargs):
        args = kwargs
        if cls == Speech:
            args['title'] = self.title
            args['start_date'] = self.start_date

        s = cls(instance=self.instance, **args)
        if self.commit:
            s.save()
        elif s.title:
            print >> sys.stderr, s.title
        return s

    def get_tag(self, node):
        return etree.QName(node.tag).localname

    def get_text(self, node):
        paras = [etree.tostring(child, method='text') 
                for child in node.iterchildren() 
                if self.get_tag(child) != 'from']
        return '\n\n'.join(paras)

    def name_display(self, name):
        match = name_rx.match(name)
        if match:
            honorific, fname, party, _ = match.groups()
            display_name = '%s %s%s' % (honorific, fname.title(), party if party else '')
            return display_name
        else:
            return name.title()

    def get_person(self, name):
        cached = self.person_cache.get(name, None)
        if cached:
            return cached

        display_name = self.name_display(name) if name else '(narrative)'

        speaker = None
        popit_person = None

        if name:
            self.speakers_count += 1
            popit_person = self.get_popit_person(display_name)

            if popit_person:
                self.speakers_matched += 1
                try:
                    speaker = Speaker.objects.get(
                        instance = self.instance, 
                        person = popit_person)
                except Speaker.DoesNotExist:
                    pass
            else:
                print >> sys.stderr, " - Failed to get user %s" % display_name

        if not speaker:
            speaker, _ = Speaker.objects.get_or_create(
                instance = self.instance, 
                name = display_name)

            if popit_person:
                speaker.person = popit_person
                speaker.save()

        self.person_cache[name] = speaker
        return speaker

    def get_popit_person(self, name):

        def _get_popit_person(name):
            person = self.get_best_popit_match(name, self.already_spoken, 0.75)
            if person:
                return person

            person = self.get_best_popit_match(name, self.persons.values(), 0.80)
            if person:
                self.already_spoken.append(person)
                return person

        person = _get_popit_person(name)
        if person:
            ret = Person.update_from_api_results(instance=self.ai, doc=person)
            return ret
            # return Person.update_from_api_results(instance=self.instance, doc="HELLO")
        
        return None

    def get_best_popit_match(self, name, possible, threshold):
        #TODO: here
        honorific = ''
        party = ''
        match = name_rx.match(name)

        if match:
            honorific, name, _, party = match.groups()

        def _get_initials(record):
            initials = record.get('initials', None)
            if initials:
                return initials
            given_names = record.get('given_names', None)
            if given_names:
                initials = [a[:1] for a in given_names.split()]
                return ' '.join(initials)
            return ''

        def _match(record):
            if name == record.get('name', ''):
                return 1.0

            name_with_initials = '%s %s' % (
                _get_initials(record),
                record.get('family_name', ''))
            if name.lower() == name_with_initials.lower():
                return 0.9

            
            canon_rx = re.compile(r'((the|of|for|and)\b ?)')
            valid_chars = string.letters + ' '
            def _valid_char(c):
                return c in valid_chars
            def _canonicalize(name):
                return filter(_valid_char, canon_rx.sub('', name.lower()))

            for m in record['memberships']:
                role = m.get('role', '')
                if role:
                    cname = _canonicalize(name)
                    crole = _canonicalize(role)
                    if crole == cname:
                        return 0.9

                    if cname[-7:] == 'speaker':
                        if crole == ('%s national assembly' % cname):
                            return 0.8

            return 0

        for p in possible:
            score = _match(p)
            if score >= threshold:
                return p

        return None

    def visit(self, node, section):
       for child in node.iterchildren():
            tagname = self.get_tag(child)
            if tagname == 'heading':
                # this will already have been extracted
                continue
            if tagname == 'debateSection':
                title = child.heading.text.title()
                childSection = self.make(Section, parent=section, title=title)
                self.visit(child, childSection)
            elif tagname == 'speech':
                text = self.get_text(child)
                name = child['from'].text
                speaker = self.get_person( name )
                speech = self.make(Speech,
                        section = section,
                        # title
                        # event
                        # location
                        # speaker
                        # {start,end}_{date,time}
                        # tags
                        # source_url
                        text = text,
                        speaker = speaker,
                        speaker_display = self.name_display(name),
                        )
            else:
                text = etree.tostring(child, method='text')
                speaker = self.get_person(None)
                speech = self.make(Speech,
                        section = section,
                        # title
                        # event
                        # location
                        # speaker # UNKNOWN
                        # {start,end}_{date,time}
                        # tags
                        # source_url
                        text = text,
                        speaker = speaker,
                        )
