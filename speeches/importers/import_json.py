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
# "speeches": [
#  {
#   "personname": "M Johnson",
#   "party": "ANC",
#   "text": "Mr M Johnson (ANC) chaired the meeting."
#  },
#  ...
#  ],
# "date": "2013-06-21",
# "organization": "Agriculture, Forestry and Fisheries",
# "reporturl": "http://www.pmg.org.za/report/20130621-report-back-from-departments-health-trade-and-industry-and-agriculture-forestry-and-fisheries-meat-inspection",
# "title": "Report back from Departments of Health, Trade and Industry, and Agriculture, Forestry and Fisheries on meat inspection services and labelling in South Africa",
## "committeeurl": "http://www.pmg.org.za/committees/Agriculture,%20Forestry%20and%20Fisheries"
#}

class ImportJson (ImporterBase):

    def import_document(self, document_path):

        data = json.load( open(document_path, 'r') )

        meetingdate_string = data.get( 'date', None )
        meetingdate = None
        if meetingdate_string:
            meetingdate = datetime.strptime( meetingdate_string, '%Y-%m-%d' ).date()

        self.init_popit_data(date=meetingdate)

        self.title = data.get( 'title', data.get('organization', '') )

        section = self.make(Section, title=self.title)

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

                    location = s.get('location', ''),
                    title    = s.get('title', ''),
                    event    = s.get('event', ''),
                    source_url = s.get('source_url', ''),
                    # {start,end}_{date,time}
            )

            for tagname in s.get('tags', []):
                (tag,_) = Tag.objects.get_or_create( name=tagname, instance=self.instance )
                speech.tags.add(tag)

        return section
