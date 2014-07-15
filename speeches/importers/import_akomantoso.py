# -*- coding: utf-8 -*-

import logging

from dateutil import parser as dateutil
from lxml import etree
from lxml import objectify

from speeches.importers.import_base import ImporterBase
from speeches.models import Section, Speech, Speaker

logger = logging.getLogger(__name__)


class ImportAkomaNtoso (ImporterBase):
    start_date = None

    def import_document(self, document_path):
        tree = objectify.parse(document_path)
        self.xml = tree.getroot()
        self.ns = self.xml.nsmap.get(None, None)
        return self.parse_document()

    def parse_document(self):
        debate = self.xml.debate

        if self.ns:
            people = debate.findall(
                'an:meta/an:references/an:TLCPerson',
                namespaces={'an': self.ns},
                )
        else:
            people = debate.findall('meta/references/TLCPerson')
        if people is None:
            people = []
        for person in people:
            id = person.get('id')
            href = person.get('href')
            try:
                speaker = Speaker.objects.get(
                    instance=self.instance, identifiers__identifier=href)
            except Speaker.DoesNotExist:
                speaker = Speaker(
                    instance=self.instance, name=person.get('showAs'))
                if self.commit:
                    speaker.save()
                    speaker.identifiers.create(
                        identifier=href, scheme='Akoma Ntoso import')

            self.speakers[id] = speaker

        if self.ns:
            docDate = debate.xpath(
                'an:coverPage//an:docDate|an:preface//an:docDate',
                namespaces={'an': self.ns},
                )
        else:
            docDate = debate.xpath('coverPage//docDate|preface//docDate')
        if docDate:
            self.start_date = dateutil.parse(docDate[0].get('date'))

        if self.ns:
            docTitle = debate.xpath(
                'an:coverPage//an:docTitle|an:preface//an:docTitle',
                namespaces={'an': self.ns},
                )
        else:
            docTitle = debate.xpath('coverPage//docTitle|preface//docTitle')
        if docTitle:
            section = self.make(Section, parent=None, title=docTitle[0].text)
        else:
            section = None

        self.visit(debate.debateBody, section)

    def get_tag(self, node):
        return etree.QName(node.tag).localname

    def get_text(self, node):
        paras = [node.text]
        paras += [
            etree.tostring(child, encoding='utf-8').decode('utf-8')
            for child in node.iterchildren()
            if self.get_tag(child) not in ('num', 'heading', 'subheading', 'from')
            ]
        return ''.join(filter(None, paras))

    def construct_title(self, node):
        title = []
        if hasattr(node, 'num'):
            title.append(node.num.text)
        if hasattr(node, 'heading'):
            title.append(node.heading.text)
        if hasattr(node, 'subheading'):
            title.append(node.subheading.text)
        title = ' '.join(title)
        return title

    def construct_datetime(self, time):
        if not time:
            return (None, None)
        dt = dateutil.parse(time)
        return dt.date(), dt.time()

    def get_speaker(self, child):
        if child.find('from'):
            display_name = child['from'].text
        else:
            display_name = None

        by_ref = child.get('by')
        if by_ref:
            if not by_ref.startswith('#'):
                logger.warn(
                    "by attribute value doesn't begin with '#': %s" % by_ref)
            speaker = self.speakers[by_ref[1:]]
        else:
            speaker = None

        return speaker, display_name

    def handle_tag(self, node, section):
        """If we need to do something out of the ordinary handling elements,
        subclass it here"""
        return False

    def visit(self, node, section):
        for child in node.iterchildren():
            tagname = self.get_tag(child)
            if tagname in ('num', 'heading', 'subheading'):
                # this will already have been extracted
                continue
            if tagname in (
                    'debateSection', 'administrationOfOath', 'rollCall',
                    'prayers', 'oralStatements', 'writtenStatements',
                    'personalStatements', 'ministerialStatements',
                    'resolutions', 'nationalInterest', 'declarationOfVote',
                    'communication', 'petitions', 'papers', 'noticesOfMotion',
                    'questions', 'address', 'proceduralMotions',
                    'pointOfOrder', 'adjournment',
                    ):
                title = self.construct_title(child)
                childSection = self.make(Section, parent=section, title=title)
                self.visit(child, childSection)
            elif tagname in ('speech', 'question', 'answer'):
                title = self.construct_title(child)
                text = self.get_text(child)
                start_date, start_time = self.construct_datetime(child.get('startTime'))
                end_date, end_time = self.construct_datetime(child.get('endTime'))
                speaker, display_name = self.get_speaker(child)
                self.make(
                    Speech,
                    section=section,
                    title=title,
                    start_date=start_date or self.start_date,
                    start_time=start_time,
                    end_date=end_date,
                    end_time=end_time,
                    text=text,
                    speaker=speaker,
                    speaker_display=display_name,
                    )
            elif tagname in ('scene', 'narrative', 'summary', 'other'):
                text = self.get_text(child)

                self.make(
                    Speech,
                    section=section,
                    start_date=self.start_date,
                    text=text,
                    )
            else:
                success = self.handle_tag(child, section)
                if not success:
                    logger.error(
                        '%s unrecognised, "%s" - %s' %
                        (child.tag, child, self.get_text(child))
                        )
