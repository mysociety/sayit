#!/usr/bin/env python

from scsl.scrape import get_transcripts
from scsl.parse import parse_transcript
from utils import *

class SCSLParser(BaseParser):
    instance = 'charles-taylor'

    def skip_transcript(self, data):
        if data['date'].isoformat() == '2006-07-21': return True # Is garbled
        return False

    def get_transcripts(self):
        return get_transcripts()

    def parse_transcript(self, data):
        return parse_transcript(data['text'], data['date'])

    def prettify(self, s):
        s = s.title()
        s = s.replace('Dct-', 'DCT-').replace('Tfi-', 'TF1-').replace('Tf1-', 'TF1-')
        return s

parser = SCSLParser()
parser.run()
