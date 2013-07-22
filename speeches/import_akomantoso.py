import calendar
import datetime
import logging
import os, sys

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

    def make(self, cls, **kwargs):
        s = cls(instance=self.instance, **kwargs)
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

            title = '%s (%s)' % (
                    mainSection.heading.text, 
                    etree.tostring(xml.debate.preface.p, method='text'))

            section = self.make(Section, title=title)

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

    def get_person(self, name):
        # TODO, popit lookup
        speaker, _ = Speaker.objects.get_or_create(name=name, instance=self.instance)
        return speaker

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
                speaker = self.get_person( '(narrative)' )
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
