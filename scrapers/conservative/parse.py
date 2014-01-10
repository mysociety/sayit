from datetime import datetime
import re

def parse_speech(page, speaker):
    if page.find('div', 'titlebarpage'):
        text = page.find('div', id='bodyarea')
        text.find('h1', 'maintitle').extract()
        im = text.find('div', 'floatleftim')
        if im: im.extract()
        text = text.decode_contents().strip()
        text = re.sub('<h2 class="subtitle">(.*?)</h2>', r'<strong>\1</strong>', text)
        text = text.replace('</p><p>', '\n\n')
        text = text.replace('<br/>', '\n')
        text = re.sub('</?p>', '\n', text).strip()
    elif page.find('h2', 'leader'):
        speaker_and_date = page.find('h3', 'info').decode_contents()
        speaker, date = re.match('\s*(.*?)\s*, (.*)$', speaker_and_date).groups()
        date = datetime.strptime(date, '%A, %B %d %Y').date()
        text = page.find('div', 'txt').decode_contents()
        text = re.sub('</?p[^>]*>', '\n', text)
    else:
        raise Exception

    text = re.sub('\n\n+', '\n\n', text)
    speaker = re.sub(' ME?P', '', speaker)
    speaker = re.sub('(The )?(Rt )?Hon ', '', speaker)
    return text, speaker
