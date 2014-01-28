# -*- coding: utf-8 -*-

import logging

from lxml import etree
from lxml import objectify

from speeches.importers.import_base import ImporterBase
from speeches.models import Section, Speech

logger = logging.getLogger(__name__)

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
        paras = [ node.text ]
        paras += [ etree.tostring(child, encoding='utf-8')
                    for child in node.iterchildren()
                    if self.get_tag(child) not in ('num', 'heading', 'subheading', 'from') ]
        return ''.join(filter(None, paras))

    def name_display(self, name):
        return name

    def construct_title(self, node):
        title = []
        if hasattr(node, 'num'):
            title.append(node.num.text)
        if hasattr(node, 'heading'):
            title.append(node.heading.text)
        if hasattr(node, 'subheading'):
            title.append(node.subheading.text)
        title = ' '.join(title)
        if self.title_case:
            title = title_case_heading(title)
        return title

    def visit(self, node, section):
       for child in node.iterchildren():
            tagname = self.get_tag(child)
            if tagname in ('num', 'heading', 'subheading'):
                # this will already have been extracted
                continue
            if tagname in ('debateSection', 'administrationOfOath', 'rollCall',
                    'prayers', 'oralStatements', 'writtenStatements',
                    'personalStatements', 'ministerialStatements',
                    'resolutions', 'nationalInterest', 'declarationOfVote',
                    'communication', 'petitions', 'papers', 'noticesOfMotion',
                    'questions', 'address', 'proceduralMotions',
                    'pointOfOrder', 'adjournment'):
                title = self.construct_title(child)
                childSection = self.make(Section, parent=section, title=title)
                self.visit(child, childSection)
            elif tagname in ('speech', 'question', 'answer'):
                title = self.construct_title(child)
                text = self.get_text(child)
                display_name = self.name_display(child['from'].text)
                speaker = self.get_person(display_name)
                speech = self.make(Speech,
                        section = section,
                        title = title,
                        start_date = self.start_date,
                        text = text,
                        speaker = speaker,
                        speaker_display = display_name,
                )
            elif tagname in ('scene', 'narrative', 'summary', 'other'):
                text = self.get_text(child)
                speaker = self.get_person(None)
                speech = self.make(Speech,
                        section = section,
                        start_date = self.start_date,
                        text = text,
                        speaker = speaker,
                )
            else:
                raise Exception, '%s unrecognised, "%s" - %s' % (child.tag, child, self.get_text(child))
