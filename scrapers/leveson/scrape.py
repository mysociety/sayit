#!/usr/bin/env python

from datetime import datetime
import os
import re
import subprocess

import bs4
import requests
import requests_cache

BASE_DIR = os.path.dirname(__file__)
requests_cache.install_cache(os.path.join(BASE_DIR, 'data', 'leveson'))

def get_url(url, type='none'):
    """Fetches a URL from the Leveson Inquiry website, and returns either its
       text, soup or content."""
    if url[0] == '/': url = 'http://www.levesoninquiry.org.uk' + url
    resp = requests.get(url)
    if type == 'binary':
        return resp.content
    elif type == 'html':
        return bs4.BeautifulSoup(resp.text)
    return resp.text

def convert_four_up_pdf(text):
    # Remove header/footer from all pages
    text = re.sub('\014?Leveson Inquiry Initial Hearing +4 October 2011', '', text)
    text = re.sub('\(\+44\) 207 404 1400 +London EC4A 2DY', '', text)
    text = re.sub('Merrill Legal Solutions +www.merrillcorp/mls.com +8th Floor 165 Fleet Street', '', text)
    text = re.sub(' *\d+ \(Pages \d+ to \d+\)', '', text)

    # Loop through, slurping up the pages by page number
    text_l, text_r = [], []
    pages = {}
    text = re.split('\r?\n', text)
    for line in text:
        if re.match('\s*$', line): continue
        if 'INDEX' in line: break

        m = re.match(r' +Page (\d+)(?: +Page (\d+))?', line)
        if m:
            page_l = int(m.group(1))
            pages[page_l] = text_l
            if m.group(2):
                page_r = int(m.group(2))
                pages[page_r] = text_r
            text_l, text_r = [], []
            continue

        # Left and right pages
        m = re.match(r' +(\d+)( .*) +\1( .*)?$', line)
        if m:
            line_n = int(m.group(1))
            line_l = '       %s' % m.group(2).rstrip()
            line_r = '       %s' % m.group(3) if m.group(3) else ''
            text_l.append('%2d%s' % (line_n, line_l))
            text_r.append('%2d%s' % (line_n, line_r))
            continue
        # Just left page at the end
        m = re.match(r' +(\d+)( .*)?$', line)
        line_n = int(m.group(1))
        line_l = '       %s' % m.group(2) if m.group(2) else ''
        text_l.append('%2d%s' % (line_n, line_l))

    # Reconstruct in page order for normal processing
    text = ''
    for num, page in sorted(pages.items()):
        for line in page:
            text += line + '\n'
        text += '    %d\n\014\n' % num
    return text

def convert_pdf_transcript(transcripts, url):
    pdf_transcript = [ t for t in transcripts if 'pdf' in t.get('href') ][0]
    pdf_url = pdf_transcript.get('href')
    file_pdf = os.path.join(BASE_DIR, 'data', os.path.basename(pdf_url))
    file_text = file_pdf.replace('.pdf', '.txt')
    if not os.path.exists(file_text):
        pdf_transcript = get_url(pdf_url, 'binary')
        fp = open(file_pdf, 'w')
        fp.write(pdf_transcript)
        fp.close()
        subprocess.call([ 'pdftotext', '-layout', file_pdf ])
        file_patch = file_pdf.replace('.pdf', '.patch')
        if os.path.exists(file_patch):
            inn = open(file_patch)
            subprocess.call([ 'patch', '--backup', file_text ], stdin=inn)
            inn.close()
    text = open(file_text).read()

    if '2011-10-04' in url:
        # This PDF uses 4-up layout unlike the other two
        text = convert_four_up_pdf(text)
    else:
        text = text.replace('Leveson Inquiry transcript www.levesoninquiry.org.uk', '')

    # Be sure to have ^L on its own line
    text = text.replace('\014', '\014\n')

    return text

def get_transcript(url):
    hearing = get_url(url, 'html')
    transcripts = hearing.find(id='transcript-col').find_all('a')
    text_transcripts = [ t for t in transcripts if 'txt' in t.get('href') ]
    if len(text_transcripts):
        text = get_url( text_transcripts[0].get('href') )
    else:
        # Three oldest do not have text transcripts
        text = convert_pdf_transcript(transcripts, url)

    # Return an array of lines
    return re.split('\r?\n', text)

def get_transcripts():
    hearings = get_url('/hearings/', 'html')
    # Loop through the rows in reverse order (so oldest first)
    for row in reversed(hearings('tr')):
        date, am, pm = row('td')
        date = datetime.strptime(date.string, '%A %d %B %Y').date()
        for link in am.a, pm.a:
            if not link: continue
            url = link.get('href')
            yield {
                'date': date,
                'url': url,
                'text': get_transcript(url),
            }
