from django.test import TestCase

from speeches.models import Speech, Speaker

class SmokeTests(TestCase):
    """Simple smoke tests (is it up?) of all the urls on the site"""

    def test_home_page(self):
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)

    def test_all_speakers_page(self):
        resp = self.client.get('/speeches')
        self.assertEqual(resp.status_code, 200)

    def test_a_speaker_page(self):
        # Add a speaker first
        speaker = Speaker.objects.create(popit_url='http://popit.mysociety.org/api/v1/person/abcd', name='Steve')
        resp = self.client.get('/speaker/%s' % speaker.id)
        self.assertEqual(resp.status_code, 200)

    def test_a_speech_page(self):
        # Add a speech first
        speech = Speech.objects.create(text='Testing speech page')
        resp = self.client.get('/speech/%s' % speech.id)
        self.assertEqual(resp.status_code, 200)

    def test_add_speech_page(self):
        resp = self.client.get('/speech/add')
        self.assertEqual(resp.status_code, 200)