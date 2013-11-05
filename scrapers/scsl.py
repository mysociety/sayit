#!/usr/bin/env python

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
os.environ['DJANGO_SETTINGS_MODULE'] = 'spoke.settings'
import optparse

from instances.models import Instance
from speeches.models import Section, Speaker, Speech

from scsl.scrape import get_transcripts
from scsl.parse import parse_transcript
from scsl.utils import prettify

# Command line options
from optparse import OptionParser
parser = OptionParser()
parser.add_option('--commit', dest='commit', help='commit to database', action='store_true')
(options, args) = parser.parse_args()
commit = options.commit

# Special get_or_create that won't always commit
def get_or_create(model, **attrs):
    global commit
    try:
        obj = model.objects.get(**attrs)
    except model.DoesNotExist:
        obj = model(**attrs)
        if commit:
            obj.save()
    return obj

# First we need an instance
instance = get_or_create(Instance, label='charles-taylor')

# And then we need to parse some transcripts
for date, url, text in get_transcripts():
    date_section = get_or_create(Section, instance=instance, title='Hearing, %s' % date.strftime('%d %B %Y').lstrip('0'))

    if date.isoformat() == '2006-07-21': continue # Is garbled

    for speech in parse_transcript(text, date):
        if not speech: continue
        if speech.section:
            section = get_or_create(Section, instance=instance, title=prettify(speech.section.title), parent=date_section)
        else:
            section = date_section
        if speech.speaker:
            speaker = prettify(speech.speaker)
            speaker = get_or_create(Speaker, instance=instance, name=speaker)
        else:
            speaker = None
        text = '\n\n'.join([ ' '.join(s) for s in speech.text ])
        #print speech.section, speaker, text
        speech = Speech(instance=instance, section=section, text=text, speaker=speaker, start_date=date, start_time=speech.time)
        if commit:
            speech.save()
