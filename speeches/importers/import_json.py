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

from speeches.models import Section, Speech, Speaker

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
# "meetingdate": "21 Jun 2013",
# "committeename": "Agriculture, Forestry and Fisheries",
# "reporturl": "http://www.pmg.org.za/report/20130621-report-back-from-departments-health-trade-and-industry-and-agriculture-forestry-and-fisheries-meat-inspection",
# "report": "Report back from Departments of Health, Trade and Industry, and Agriculture, Forestry and Fisheries on meat inspection services and labelling in South Africa",
# "committeeurl": "http://www.pmg.org.za/committees/Agriculture,%20Forestry%20and%20Fisheries"
#}

class ImportJson (ImporterBase):

    def import_document(self, document_path):

        data = json.load( open(document_path, 'r') )

        meetingdate_string = data.get( 'meetingdate', None )
        meetingdate = datetime.strptime( meetingdate_string, '%d %b %Y' ).date()

        self.init_popit_data(date=meetingdate)

        self.title = data.get( 'report', data.get('committeename', '') )

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
                    # title
                    # event
                    # location
                    # speaker
                    # {start,end}_{date,time}
                    # tags
                    # source_url
                    speaker = speaker,
                    speaker_display = display_name,
            )

        return section
