#!/usr/bin/env python

from datetime import datetime
import os
import re

import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
os.environ['DJANGO_SETTINGS_MODULE'] = 'spoke.settings'
from instances.models import Instance
from speeches.models import Section, Speaker, Speech

from leveson.scrape import get_transcripts
from leveson.parse import parse_transcript

commit = True
def get_or_create(model, **attrs):
    global commit
    try:
        obj = model.objects.get(**attrs)
    except model.DoesNotExist:
        obj = model(**attrs)
        if commit:
            obj.save()
    return obj

instance = get_or_create(Instance, label='leveson')

for date, url, text in get_transcripts():
    if '2011-11-21pm' in url: continue # Included in the morning
    if '2011-12-15am' in url: continue # Included in the afternoon
    date_section = get_or_create(Section, instance=instance, title='Hearing, %s' % date.strftime('%d %B %Y').lstrip('0'))

    for speech in parse_transcript(text, url):
        if not speech: continue
        if speech.section:
            section = get_or_create(Section, instance=instance, title=speech.section.title, parent=date_section)
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
