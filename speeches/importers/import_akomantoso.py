# -*- coding: utf-8 -*-

import logging

from dateutil import parser as dateutil
from lxml import etree
from lxml import objectify
from six.moves.urllib.request import urlopen

from speeches.importers.import_base import ImporterBase
from speeches.models import Section, Speech, Speaker

logger = logging.getLogger(__name__)


class ImportAkomaNtoso (ImporterBase):
    start_date = None

    def import_document(self, document_path):
        if document_path.startswith('http'):
            self.xml = objectify.fromstring(urlopen(document_path).read())
        else:
            self.xml = objectify.parse(document_path).getroot()
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

        docDate = self.get_preface_tag(debate, 'docDate')
        if docDate:
            self.start_date = dateutil.parse(docDate.get('date'))

        docTitle = self.get_preface_tag(debate, 'docTitle')
        if docTitle:
            docTitle = docTitle.text

        docNumber = self.get_preface_tag(debate, 'docNumber')
        if docNumber:
            docNumber = docNumber.text

        legislature = self.get_preface_tag(debate, 'legislature')
        if legislature:
            legislature = legislature.text

        session = self.get_preface_tag(debate, 'session')
        if session:
            session = session.text

        source_url = self.get_preface_tag(debate, 'link') or ''
        if source_url:
            source_url = source_url.get('href')

        section = None
        if docTitle:
            kwargs = {
                'parent': None,
                'heading': docTitle,
                'start_date': self.start_date,
                'number': docNumber or '',
                'legislature': legislature or '',
                'session': session or '',
            }

            # If the importer has no opinion on clobbering, just import the section,
            # potentially creating a duplicate section.
            if self.clobber is not None:
                try:
                    section = Section.objects.for_instance(self.instance).get(**kwargs)
                    if self.clobber:
                        logger.info('Clobbering %s' % docTitle)
                        for speech in section.descendant_speeches():
                            speech.delete()
                        section.delete()
                    else:
                        logger.info('Skipping %s' % docTitle)
                        return
                except Section.DoesNotExist:
                    logger.info('Importing %s' % docTitle)

            section = self.make(Section, source_url=source_url, **kwargs)

        self.visit(debate.debateBody, section)

    def get_preface_tag(self, debate, tag):
        if self.ns:
            tag = debate.xpath('an:coverPage//an:%s|an:preface//an:%s' % (tag, tag), namespaces={'an': self.ns})
        else:
            tag = debate.xpath('coverPage//%s|preface//%s' % (tag, tag))
        if tag:
            return tag[0]

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

    def construct_heading(self, node):
        headings = {}
        for tag in ('num', 'heading', 'subheading'):
            if hasattr(node, tag):
                headings[tag] = getattr(node, tag).text
        return headings

    def construct_datetime(self, time):
        if not time:
            return (None, None)
        dt = dateutil.parse(time)
        return dt.date(), dt.time()

    def get_speaker(self, child):
        if hasattr(child, 'from'):
            display_name = child['from'].text
        else:
            display_name = None

        by_ref = child.get('by')
        speaker = None
        if by_ref:
            if not by_ref.startswith('#'):
                logger.warn(
                    "by attribute value doesn't begin with '#': %s" % by_ref)
            try:
                speaker = self.speakers[by_ref[1:]]
            except KeyError:
                logger.warn("ID %s in speech has no corresponding TLCPerson entry" % by_ref)

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
                headings = self.construct_heading(child)
                childSection = self.make(
                    Section,
                    parent=section,
                    start_date=self.start_date,
                    **headings
                )
                self.visit(child, childSection)
            elif tagname in ('speech', 'question', 'answer'):
                headings = self.construct_heading(child)
                text = self.get_text(child)
                start_date, start_time = self.construct_datetime(child.get('startTime'))
                end_date, end_time = self.construct_datetime(child.get('endTime'))
                speaker, display_name = self.get_speaker(child)
                self.make(
                    Speech,
                    section=section,
                    start_date=start_date or self.start_date,
                    start_time=start_time,
                    end_date=end_date,
                    end_time=end_time,
                    text=text,
                    speaker=speaker,
                    speaker_display=display_name,
                    type=tagname,
                    **headings
                    )
            elif tagname in ('scene', 'narrative', 'summary', 'other'):
                text = self.get_text(child)

                self.make(
                    Speech,
                    section=section,
                    start_date=self.start_date,
                    text=text,
                    type=tagname,
                    )
            else:
                success = self.handle_tag(child, section)
                if not success:
                    logger.error(
                        '%s unrecognised, "%s" - %s' %
                        (child.tag, child, self.get_text(child))
                        )
