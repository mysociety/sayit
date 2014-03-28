from datetime import datetime
import os
import re
import subprocess

import bs4
import requests_cache

BASE_DIR = os.path.dirname(__file__)

session = requests_cache.core.CachedSession(os.path.join(BASE_DIR, 'taylor'))
session_day = requests_cache.core.CachedSession(os.path.join(BASE_DIR, 'taylor'), expire_after=86400)

def get_url(url, type='none', session=session):
    """Fetches a URL from the SC-SL website, and returns either its
       text, soup or content."""
    if url[0] == '/': url = 'http://www.sc-sl.org' + url
    resp = session.get(url)
    if resp.status_code != 200:
        raise Exception
    if type == 'binary':
        return resp.content
    elif type == 'html':
        return bs4.BeautifulSoup(resp.text)
    return resp.text

def get_transcript(url, date):
    file_pdf = os.path.join(BASE_DIR, 'data', date.isoformat()+'.pdf')
    file_text = file_pdf.replace('.pdf', '.txt')
    if not os.path.exists(file_text):
        hearing = get_url(url, 'binary')
        fp = open(file_pdf, 'w')
        fp.write(hearing)
        fp.close()
        subprocess.call([ 'pdftotext', '-layout', file_pdf ])
    text = open(file_text).read()

    # Be sure to have ^L on its own line
    text = text.replace('\014', '\014\n')
    # Return an array of lines
    return re.split('\r?\n', text)

def get_transcripts():
    transcripts = get_url('/CASES/ProsecutorvsCharlesTaylor/Transcripts/tabid/160/Default.aspx', 'html', session=session_day)
    # Loop through the rows in reverse order (so oldest first)
    for row in transcripts('p'):
        for thing in row.findAll(text=re.compile('\d')):
            text = thing.strip()
            if re.match('\d+$', text):
                link = thing.find_parent('a')
                date = date.replace(day=int(text))
                url = link['href'].replace(' ', '%2B').replace('+', '%2B')

                if 'tabid/160/www.sc-sl.org' in url:
                    url = re.sub('.*www', 'www', url)
                if url[0:3] == 'www':
                    url = 'http://%s' % url

                # Wrong date on index page
                if date.isoformat() == '2009-06-09':
                    date = date.replace(day=8)

                yield {
                    'date': date,
                    'url': url,
                    'text': get_transcript(url, date),
                }

            else:
                date = datetime.strptime(thing, '%B %Y').date()
