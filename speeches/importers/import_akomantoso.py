# -*- coding: utf-8 -*-

import logging
import re

from lxml import etree
from lxml import objectify

from speeches.importers.import_base import ImporterBase
from speeches.models import Section, Speech

logger = logging.getLogger(__name__)
name_rx = re.compile(r'^(\w+) (.*?)( \((\w+)\))?$')

def title_case_heading(heading):
    titled = heading.title()
    titled = titled.replace("'S", "'s").replace("’S", "’s")
    return titled

class ImportAkomaNtoso (ImporterBase):
    title_case = False
    start_date = None

    def import_document(self, document_path):
        tree = objectify.parse(document_path)
        self.xml = tree.getroot()
        return self.parse_document()

    def parse_document(self):
        self.visit(self.xml.debate.debateBody, None)

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
            if self.title_case:
                fname = fname.title()
            display_name = '%s %s%s' % (honorific, fname, party if party else '')
            # XXX Now the sayit project indexes stop words, this next line keeps
            # the test passing. This should be looked at at some point.
            # "The" is not an honorific anyway, should we be here?.
            display_name = re.sub('^The ', '', display_name)
            return display_name
        else:
            if self.title_case:
                name = name.title()
            return name

    def visit(self, node, section):
       for child in node.iterchildren():
            tagname = self.get_tag(child)
            if tagname == 'heading':
                # this will already have been extracted
                continue
            if tagname == 'debateSection':
                title = child.heading.text
                if self.title_case:
                    title = title_case_heading(title)
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
                        start_date = self.start_date,
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
                        start_date = self.start_date,
                        text = text,
                        speaker = speaker,
                        )
