#!/usr/bin/env python

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
os.environ['DJANGO_SETTINGS_MODULE'] = 'spoke.settings'
import optparse

from instances.models import Instance
from speeches.models import Section, Speaker, Speech

from conservative.scrape import get_speeches
from conservative.parse import parse_speech

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
instance = get_or_create(Instance, label='old-conservative-speeches')

# And then we need to parse some transcripts
for url, date, title, speaker, text in get_speeches():
    text, speaker = parse_speech(text, speaker)
    speaker = get_or_create(Speaker, instance=instance, name=speaker)
    speech = Speech(instance=instance, text=text, speaker=speaker, start_date=date, title=title, source_url=url)
    if commit:
        speech.save()
