#!/usr/bin/env python

import datetime
import itertools
import os
import re
import urlparse

import requests_cache

from utils import BaseParser
from utils import ParserSpeech as Speech, ParserSection as Section

INSTANCE = 'federal-reserve'
BASE_DIR = os.path.dirname(__file__)

months = '(?:January|February|March|April|May|June|July|August|September|October|November|December)'

def prevnext(it):
    prev, curr, next = itertools.tee(it, 3)
    prev = itertools.chain([None], prev)
    next = itertools.chain(itertools.islice(next, 1, None), [None])
    return itertools.izip(prev, curr, next)

class FedParser(BaseParser):
    instance = INSTANCE
    requests = requests_cache.core.CachedSession(os.path.join(BASE_DIR, 'data', INSTANCE))

    def get_transcripts(self):
        for y in range(2008, 2001, -1):
            url_index = 'http://www.federalreserve.gov/monetarypolicy/fomchistorical%d.htm' % y
            index = self.get_url(url_index, 'html')
            for sesh in reversed(index(class_='year')):
                url = sesh.find_parent('table').find(text=re.compile('Transcript')).parent['href']
                url = urlparse.urljoin(url_index, url)
                title = sesh.find(text=True).split(None, 2)
                title = '%s, %s %s %s' % (title[2], title[1], title[0], y)
                yield { 'year': y, 'title': title, 'url': url, 'text': self.get_pdf(url) }

    def top_section_title(self, data):
        return data['title']

    def parse_transcript(self, data):
        print "PARSING %s" % data['url']

        speech = None
        new_page = False
        started = False
        ignore_rest_of_page = False
        Speech.reset(True)

        for prev_line, line, next_line in prevnext(data['text']):
            # Page break
            if '\014' in line:
                continue

            # Empty line
            if re.match('\s*$', line):
                continue

            # Page number
            m = re.match('%s (?:\d+|\d+...\d+), 200\d *(\d+) of (\d+)$' % months, line)
            if m:
                page = int(m.group(1))
                new_page = True
                ignore_rest_of_page = False
                continue

            # Message about lunch/adjournments
            m = re.match(' {10,}(\[.*\])$', line)
            if m:
                yield speech
                speech = Speech( speaker=None, text=line )
                continue

            # Headings
            m = re.match(' {10,}(.*)$', line)
            if m:
                t = m.group(1).strip()
                if re.match('Transcript of (the )?Federal Open Market Committee (Meeting|Conference Call) (on|of)$', t):
                    started = True
                    continue
                if re.match('END OF MEETING$', t) or re.match('%s \d+-\d+, 200\d$' % months, t):
                    continue
                if re.match('%s \d+, 200\d$' % months, t):
                    Speech.current_date = datetime.datetime.strptime(t, '%B %d, %Y')
                    continue
                m = re.match('(?P<d>%s \d+(?:, 200\d)?)...(?P<s>(?:Morning|Afternoon) Session)' % months, t)
                if not m:
                    m = re.match('(?P<s>Afternoon Session)...(?P<d>%s \d+, 200\d)' % months, t)
                if m:
                    d, s = m.group('d'), m.group('s')
                    if '200' not in d:
                        d = '%s, %d' % (d, data['year'])
                    if d == 'December 15, 2008' and s == 'Morning Session':
                        d = 'December 16, 2008'
                    Speech.current_date = datetime.datetime.strptime(d, '%B %d, %Y')
                    Speech.current_section = Section( title='%s, %s' % (s, d) )
                    continue

            if not started:
                continue

            # footnote (always just "see materials")
            if re.match('[0-9]$', line):
                ignore_rest_of_page = True
            if ignore_rest_of_page:
                continue

            # Okay, here we have a non-empty, non-page number, non-heading line of just text
            # print page, line

            # New speaker
            m = re.match(' *((?:M[RS][. ]+|CHAIRMAN |VICE CHAIRMAN )[A-Z]+|PARTICIPANTS)[.:]? ?[0-9]? ?(.*)', line)
            if m:
                yield speech
                new_page = False
                speaker, speaker_display = self.fix_name(m.group(1))
                speech = Speech( speaker=speaker, text=m.group(2), speaker_display=speaker_display )
                continue

            # We must now already have a speech by the time we're here
            if not speech:
                raise Exception, 'Reached here without a speech - need to deal with "%s"' % line.strip()

            if re.match('\s*$', prev_line):
                if new_page:
                    new_page = False
                    # This line could be a continuation or a new paragraph,
                    # we're not sure as it's a new page. If the next line has
                    # the same indentation, assume it's a continuation,
                    # otherwise a new paragraph.
                    left_space = len(line) - len(line.lstrip())
                    left_space_next = len(next_line) - len(next_line.lstrip())
                    if left_space != left_space_next:
                        speech.add_para(line.strip())
                    else:
                        speech.add_text(line.strip())
                else:
                    # The previous line was blank. If the line is indented, it
                    # must be a new paragraph, in both single and double spaced
                    # text. If it's not, it must be a continuation in double
                    # spaced text.
                    if re.match(' ', line):
                        speech.add_para(line.strip())
                    else:
                        speech.add_text(line.strip())
            else:
                # If the last line wasn't blank, we're in single spaced text
                # and it must be a continuation.
                if re.search('  (Yes|No|With some reluctance, I will vote yes\.)$', line):
                    line = '<br/>' + line.strip()
                speech.add_text(line.strip())
                new_page = False

        if not started:
            raise Exception, 'Never found the title to begin'

        yield speech

    def fix_name(self, name):
        name = name.title().replace('.', '')
        name = re.sub('Mc[a-z]', lambda mo: mo.group(0)[:-1] + mo.group(0)[-1].upper(), name)
        name_fixes = {
            'Chairman Greenpan': 'Chairman Greenspan',
            'Chairman Greenpsan': 'Chairman Greenspan',
            'Chairman Greespan': 'Chairman Greenspan',
            'Mr Moscow': 'Mr Moskow',
        }
        name = name_fixes.get(name, name)
        if name == 'Mr Bernanke':
            return ('Chairman Bernanke', name)
        return (name, None)

parser = FedParser()
parser.run()

