from datetime import datetime
import os

import bs4
import requests
import requests_cache

BASE_DIR = os.path.dirname(__file__)
requests_cache.install_cache(os.path.join(BASE_DIR, 'data', 'conservatives'))

def get_url(url, type='none'):
    """Fetches a URL from the WebArchive of the Conservatives website, and
    returns either its text, soup or content."""
    if url[0] == '/': url = 'http://www.webarchive.org.uk/wayback/archive/20071115120000/http://www.conservatives.com' + url
    resp = requests.get(url)
    if type == 'binary':
        return resp.content
    elif type == 'html':
        return bs4.BeautifulSoup(resp.text)
    return resp.text

def get_speech(url):
    return get_url(url, 'html')

def get_speeches():
    # 1998-2007
    url = 'http://www.webarchive.org.uk/wayback/archive/20080907222717/http://www.conservatives.com/tile.do?def=news.speeches.page'
    pages = [ url ]
    index0 = get_url(url, 'html')
    pages += [ a['href'] for a in index0('div', class_='frontentry')[2]('a') ]
    for page in pages:
        print page
        index = get_url(page, 'html')
        main = index.find('div', id='bodyarea').findAll('div')
        i = 0
        while i < len(main):
            title = main[i]
            url = title.find('a')['href']
            title = title.string.strip()
            if not title: raise Exception
            date = datetime.strptime(main[i+1].string.strip(), '%d/%m/%Y').date()
            speaker = main[i+3].string.strip()
            if not speaker:
                if 'Hague:' in title: speaker = 'William Hague'
                if 'Yeo:' in title: speaker = 'Tim Yeo'
                if 'Willetts:' in title: speaker = 'David Willetts'
                if 'Strathclyde' in title: speaker = 'Thomas Strathclyde'
            i += 6
            yield url, date, title, speaker, get_speech(url)

    # 2008-2010
    urls = [
        # The links to speeches on the 2008 one all 404
        #'http://www.webarchive.org.uk/wayback/archive/20081209103831/http://www.conservatives.com/News/SpeechList.aspx?SearchType=NewsDate&SearchTerm=080101-081231',
        'http://www.webarchive.org.uk/wayback/archive/20091208012242/http://www.conservatives.com/News/SpeechList.aspx?SearchType=NewsDate&SearchTerm=090101-091231',
        'http://www.webarchive.org.uk/wayback/archive/20101207232023/http://www.conservatives.com/News/SpeechList.aspx?SearchType=NewsDate&SearchTerm=100101-101231',
    ]
    for url in urls:
        index = get_url(url, 'html')
        pages = index.find('ul', class_='pagination').findAll('li', class_=None)
        for page in pages:
            page_url = page.a['href']
            print page_url
            index = get_url(page_url, 'html')
            main = index.find('div', class_='results').findAll(class_='clfx')
            for div in main:
                title = div.find('a').string.strip()
                url = div.find('a')['href']
                date = div.find(class_='date').string.strip()
                date = datetime.strptime(date, '%d/%m/%y').date()
                summary = div.find('p')
                yield url, date, title, None, get_speech(url)

if __name__ == '__main__':
    for speech in get_speeches():
        pass # print speech
