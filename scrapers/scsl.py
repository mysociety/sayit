#!/usr/bin/env python

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
os.environ['DJANGO_SETTINGS_MODULE'] = 'spoke.settings'
from instances.models import Instance
from speeches.models import Section, Speaker, Speech

from scsl.scrape import get_transcripts
from scsl.parse import parse_transcript
from scsl.utils import prettify

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

instance = get_or_create(Instance, label='charles-taylor')

for date, url, text in get_transcripts():
    date_section = get_or_create(Section, instance=instance, title='Hearing, %s' % date.strftime('%d %B %Y').lstrip('0'))

    if date.isoformat() == '2010-05-19': continue # Is 2010-03-19 transcript
    if date.isoformat() == '2010-05-10': continue # Is 2010-04-19 transcript
    if date.isoformat() == '2009-08-17': continue # Is 2009-08-11 transcript
    if date.isoformat() == '2009-02-19': continue # Is 2009-01-19 transcript
    if date.isoformat() == '2008-12-04': continue # Is 2008-12-03 transcript
    if date.isoformat() == '2008-10-03': continue # Is not a transcript
    if date.isoformat() == '2008-06-25': continue # Is 2007-06-25 transcript
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
