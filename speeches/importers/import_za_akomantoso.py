# -*- coding: utf-8 -*-

from datetime import datetime
import re

from lxml import etree

from speeches.importers.import_akomantoso import ImportAkomaNtoso
from speeches.models import Section

name_rx = re.compile(r'^(\w+) (.*?)( \((\w+)\))?$')

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
