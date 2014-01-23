# -*- coding: utf-8 -*-

from datetime import datetime

from lxml import etree

from speeches.importers.import_akomantoso import ImportAkomaNtoso
from speeches.models import Section

class ImportZAAkomaNtoso (ImportAkomaNtoso):
    title_case = True

    def parse_document(self):
        """We know we only have one top level section, which we want to
        deal with differently, so do that here"""

        debate = self.xml.debate
        preface = debate.preface
        debateBody = debate.debateBody
        mainSection = debateBody.debateSection

        self.title = '%s (%s)' % (
                mainSection.heading.text,
                etree.tostring(preface.p, method='text'))

        section = self.make(Section, title=self.title)

        start_date = preface.p.docDate.get('date')
        self.set_resolver_for_date(date_string = start_date)
        self.start_date = datetime.strptime(start_date, '%Y-%m-%d')

        self.visit(mainSection, section)
        return section
