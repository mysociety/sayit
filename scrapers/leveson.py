#!/usr/bin/env python

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
os.environ['DJANGO_SETTINGS_MODULE'] = 'spoke.settings'
import optparse

from instances.models import Instance
from speeches.models import Section, Speaker, Speech

from leveson.scrape import get_transcripts
from leveson.parse import parse_transcript

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
instance = get_or_create(Instance, label='leveson')

# And then we need to parse some transcripts
for date, url, text in get_transcripts():
    if '2011-11-21pm' in url: continue # Included in the morning
    if '2011-12-15am' in url: continue # Included in the afternoon
    date_section = get_or_create(Section, instance=instance, title='Hearing, %s' % date.strftime('%d %B %Y').lstrip('0'))

    for speech in parse_transcript(text, url):
        if not speech: continue
        if speech.section:
            if speech.section.object:
                section = speech.section.object
            else:
                section = Section.objects.create(instance=instance, title=speech.section.title, parent=date_section)
                speech.section.object = section
        else:
            section = date_section
        if speech.speaker:
            speaker = get_or_create(Speaker, instance=instance, name=speech.speaker)
        else:
            speaker = None
        text = '\n\n'.join([ ' '.join(s) for s in speech.text ])
        speech = Speech(instance=instance, section=section, text=text, speaker=speaker, start_date=date, start_time=speech.time)
        if commit:
            speech.save()
