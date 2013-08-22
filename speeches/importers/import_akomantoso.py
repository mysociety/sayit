import calendar

from speeches.importers.import_base import ImporterBase, SpeechImportException
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

class ImportAkomaNtoso (ImporterBase):

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

    def get_tag(self, node):
        return etree.QName(node.tag).localname

    def get_text(self, node):
        paras = [etree.tostring(child, method='text') 
                for child in node.iterchildren() 
                if self.get_tag(child) != 'from']
        return '\n\n'.join(paras)

    def name_display(self, name):
        if not name:
            return '(narrative)'
        match = name_rx.match(name)
        if match:
            honorific, fname, party, _ = match.groups()
            display_name = '%s %s%s' % (honorific, fname.title(), party if party else '')
            return display_name
        else:
            return name.title()

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
                speaker = self.get_person( self.name_display(name) )
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
