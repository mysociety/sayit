import calendar
from datetime import datetime
import logging
import os, sys
import pickle

from lxml import etree
from lxml import objectify

from django.db import models
from django.utils import timezone

from popit.models import Person
from speeches.models import Section, Speech, Speaker

logger = logging.getLogger(__name__)

class SpeechImportException (Exception):
    pass

class ImportAkomaNtoso (object):

    def __init__(self, instance=None, commit=True):
        self.instance = instance
        self.commit = commit
        self.start_date = None
        self.title = '(untitled)'

        # TODO get this url from the AN document, if relevant
        popit_url = 'http://sa-test.matthew.popit.dev.mysociety.org/api/v0.1/'
        self.ai, _ = ApiInstance.objects.get_or_create(url=popit_url)
        self.use_cache = True

    def init_popit_data(self, date):
        # TODO this should be in popit-django.  Will try to structure things so that this
        # code can be reused there if possible!

        def add_url(collection, api_client):
            collection_url = api_client._store['base_url']
            for doc in collection:
                doc['popit_url'] = collection_url + '/' + doc['id']
            return collection

        # Stringy comparison is sufficient here
        date_string = date.strftime('%Y-%m-%d')
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

        persons = self.get_collection(ai, 'persons', add_url)
        organizations = self.get_collection(ai, 'organizations')
        memberships = self.get_collection(ai, 'memberships')

        for m in memberships:
            person = persons[m['person_id']]
            person.setdefault('memberships', [])
            person['memberships'].append(m)

            organization = persons[m['organization_id']]
            organization.setdefault('memberships', [])
            organization['memberships'].append(m)

        self.persons = persons
        self.organizations = organizations
        self.memberships = memberships
        self.already_spoken = []

    def get_collection(self, ai, collection, fn):

        pickle_path = '.' # TODO, where is sanest place to put this?
        pickle_file = os.path.jon(pickle_path, collection)

        if self.use_cache:
            try:
                collection = pickle.load(pickle_file)
                print "RARR! returning"
                return collection
            except:
                pass

        api_client = ai.api_client(collection)
        objects = api_client.get()['result']
        if fn:
            objects = fn(objects)

        objects = dict([ (doc[id], doc) for doc in objects ])

        pickle.dump(objects, pickle_file, -1)

        return objects

    def make(self, cls, **kwargs):
        args = kwargs
        if cls == Speech:
            args['title'] = self.title
            args['start_date'] = self.start_date

        s = cls(instance=self.instance, **args)
        if self.commit:
            s.save()
        elif s.title:
            print s.title
        return s

    def import_xml(self, document_path):
        try:
            tree = objectify.parse(document_path)
            xml = tree.getroot()

            debateBody = xml.debate.debateBody
            mainSection = debateBody.debateSection 

            self.title = '%s (%s)' % (
                    mainSection.heading.text, 
                    etree.tostring(xml.debate.preface.p, method='text'))

            section = self.make(Section, title=self.title)

            try:
                start_date = xml.debate.preface.p.docDate.get('date')
                self.init_popit_data(start_date)

                self.start_date = datetime.strptime(start_date, '%Y-%m-%d')

            except Exception as e:
                raise e
                # pass

            self.visit(mainSection, section)

            return section

        except Exception as e:
            raise e
            # raise SpeechImportException(str(e))

    def make(self, cls, **kwargs):
        s = cls(instance=self.instance, **kwargs)
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

    def name_display(name):
        return name.title()

    def get_person(self, name):

        popit_person = None
        if name:
            name = name_display(name)
            popit_person = self.get_popit_person(name)
        else:
            name = '(narrative)'

        speaker, _ = Speaker.objects.get_or_create(instance = self.instance, name = name)
        if popit_person:
            speaker.person = popit_person
            speaker.save()

        return speaker

    def get_popit_person(self, name):
        person = get_best_popit_match(name, self.already_spoken, 0.75)
        if person:
            return person

        person = get_best_popit_match(name, self.persons, 0.85)
        if person:
            self.already_spoken.append(person)
            return person
        
        return None

    def get_best_popit_match(self, name, possible, threshold):
        #TODO: here
        return None


    def visit(self, node, section):
       for child in node.iterchildren():
            tagname = self.get_tag(child)
            if tagname == 'heading':
                # this will already have been extracted
                continue
            if tagname == 'debateSection':
                title = child.heading.text
                childSection = self.make(Section, parent=section, title=title)
                self.visit(child, childSection)
            elif tagname == 'speech':
                text = self.get_text(child)
                speaker = self.get_person( child['from'].text )
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
