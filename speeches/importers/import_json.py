import calendar

from speeches.importers.import_base import ImporterBase, SpeechImportException
from datetime import datetime, date
import logging
import os, sys
import pickle
import re, string

import json

from django.db import models
from django.utils import timezone

from speeches.models import Section, Speech, Speaker, Tag

logger = logging.getLogger(__name__)
name_rx = re.compile(r'^(\w+) (.*?)( \((\w+)\))?$')

#{
# "parent_section_titles": [
#  "Top Section",
#  "Middle Section",
#  "Bottom Section"
# ],
# "speeches": [
#  {
#   "personname": "M Johnson",
#   "party": "ANC",
#   "text": "Mr M Johnson (ANC) chaired the meeting."
#  },
#  ...
# ],
# "public": true,
# "date": "2013-06-21",
# "organization": "Agriculture, Forestry and Fisheries",
# "reporturl": "http://www.pmg.org.za/report/20130621-report-back-from-departments-health-trade-and-industry-and-agriculture-forestry-and-fisheries-meat-inspection",
# "title": "Report back from Departments of Health, Trade and Industry, and Agriculture, Forestry and Fisheries on meat inspection services and labelling in South Africa",
## "committeeurl": "http://www.pmg.org.za/committees/Agriculture,%20Forestry%20and%20Fisheries"
#}

class ImportJson (ImporterBase):
    def __init__(self, **kwargs):
        ImporterBase.__init__(self, **kwargs)
        self.delete_existing = kwargs.get('delete_existing', False)

    def import_document(self, document_path):

        data = json.load( open(document_path, 'r') )

        start_date_string = data.get( 'date', None )
        start_date = None
        if start_date_string:
            start_date = datetime.strptime( start_date_string, '%Y-%m-%d' ).date()

        self.init_popit_data(date=start_date)

        self.title = data.get( 'title', data.get('organization', '') )
        
        # Determine if speeches should be public
        speeches_premium = data.get('premium', False)
        speeches_public = data.get('public', not speeches_premium)

        report_url = data.get('report_url', '')

        # Create parents as needed using parent_section_titles
        parent_section_titles = data.get('parent_section_titles', [])
        parent_section_titles.append(self.title)
        section = Section.objects.get_or_create_with_parents(instance=self.instance, titles=parent_section_titles)

        if self.delete_existing:
            section.speech_set.all().delete()

        for s in data.get( 'speeches', [] ):

            display_name = s['personname']
            speaker = self.get_person( display_name )

            party = s.get('party', '')
            if party:
                display_name += ' (%s)' % party

            speech = self.make(Speech,
                    text = s['text'],
                    section = section,

                    speaker = speaker,
                    speaker_display = display_name,

                    public = speeches_public,

                    location = s.get('location', ''),
                    title    = s.get('title', ''),
                    event    = s.get('event', ''),
                    source_url = s.get('source_url', report_url),

                    start_date = start_date,
                    # {start,end}_{date,time}
            )

            for tagname in s.get('tags', []):
                (tag,_) = Tag.objects.get_or_create( name=tagname, instance=self.instance )
                speech.tags.add(tag)

        return section

    def get_or_make_section(self, **kwargs):

        if self.commit:
            s, _ = Section.objects.get_or_create(instance=self.instance, **kwargs)
            return s
        else:
            # can't use get_or_create as this actually creates the objects, bah
            # (django doesn't have get_or_new?)
            s = Section(instance=self.instance, **kwargs)
            return s
