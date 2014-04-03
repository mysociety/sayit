#!/usr/bin/env python

import datetime
import os
import re

from utils import BaseParser, prevnext
from utils import ParserSpeech as Speech, ParserSection as Section

class PhilaParser(BaseParser):
    instance = 'philadelphia'

    def get_transcripts(self):
        base_url = 'http://legislation.phila.gov/transcripts/Stated%%20Meetings/%d/sm%s.pdf'
        # List manually got from http://legislation.phila.gov/council-transcriptroom/transroom_date.aspx
        transcripts = [
            '2014-03-27', '2014-03-20', '2014-03-13', '2014-03-06',
            '2014-02-27', '2014-02-20', '2014-02-06',
            '2014-01-30', '2014-01-23',
            '2013-12-12', '2013-12-05',
            '2013-11-21', '2013-11-14',
            '2013-10-31', '2013-10-24', '2013-10-17', '2013-10-10', '2013-10-03',
            '2013-09-26', '2013-09-19', '2013-09-12',
            # '2013-06-20', Won't download
            # '2013-06-13', Broken PDF
            '2013-06-06',
            '2013-05-23', '2013-05-16', '2013-05-09', '2013-05-02',
            # '2013-04-25', Broken PDF
            '2013-04-18', '2013-04-11', '2013-04-04',
            '2013-03-21', '2013-03-14', '2013-03-07',
            '2013-02-28', '2013-02-21', '2013-02-14', '2013-02-07',
            '2013-01-31', '2013-01-24',
        ]
        for date in transcripts:
            date = datetime.datetime.strptime(date, '%Y-%m-%d').date()
            url = base_url % (date.year, date.strftime('%m%d%y'))
            if date.isoformat() == '2013-03-21':
                url = base_url % (date.year, '0321b3')
                yield { 'date': date, 'url': url, 'text': self.get_pdf(url) }
                url = base_url % (date.year, '0321a3')
            yield { 'date': date, 'url': url, 'text': self.get_pdf(url) }

    def top_section_title(self, data):
        return 'Council meeting, %s' % data['date'].strftime('%d %B %Y').lstrip('0')

    def parse_transcript(self, data):
        print "PARSING %s" % data['url']

        page, num = 1, 1

        speech = None
        state = 'text'
        Speech.reset(True)

        for prev_line, line, next_line in prevnext(data['text']):
            # Page break
            if '\014' in line:
                page += 1
                num = 0
                continue

            if state == 'skip1':
                state = 'text'
                continue

            # Empty line, or line matching page footer
            if re.match('\s*$', line):
                continue
            if re.match(' *Strehlow & Associates, Inc.$| *\(215\) 504-4622$', line):
                continue

            # Ignore title page for now
            if page == 1:
                continue

            # Start of certificate/index
            if re.match(' *\d+ *(CERTIFICATE|- - -)$', line):
                state = 'index'
            if state == 'index':
                continue

            # Each page starts with page number
            if num == 0:
                m = re.match(' +(\d+)$', line)
                assert int(m.group(1)) == page
                num += 1
                continue

            # Heading somewhere within this page, just ignore it
            if num == 1:
                num += 1
                continue

            # Let's check we haven't lost a line anywhere...
            assert re.match(' *%d(   |$)' % num, line), '%s != %s' % (num, line)
            line = re.sub('^ *%d(   |$)' % num, '', line)
            num += 1

            # Narrative messages
            m = re.match(' +(\(.*\))$', line)
            if m:
                yield speech
                speech = Speech( speaker=None, text=line )
                continue
            m1 = re.match(' +(\(.*)$', line)
            m2 = re.match(' *\d+ +(.*\))$', next_line)
            if m1 and m2:
                yield speech
                speech = Speech( speaker=None, text='%s %s' % (m1.group(1), m2.group(1)) )
                state = 'skip1'
                num += 1
                continue

            # Okay, here we have a non-empty, non-page number, non-narrative line of just text
            # print page, num, line

            # New speaker
            m = re.match(" *([A-Z '.]+):(?: (.*)|$)", line)
            if m:
                yield speech
                speaker = self.fix_name(m.group(1))
                text = m.group(2) or ''
                speech = Speech( speaker=speaker, text=text )
                continue

            # We must now already have a speech by the time we're here
            if not speech:
                raise Exception, 'Reached here without a speech - need to deal with "%s"' % line

            if re.match(' ', line):
                speech.add_para(line.strip())
            else:
                speech.add_text(line.strip())

        yield speech

parser = PhilaParser()
parser.run()

