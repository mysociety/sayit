import os

from django.test import TestCase
from django.utils import simplejson

import speeches
from speeches.models import Speech, Speaker

class SpeechAPITests(TestCase):

    @classmethod
    def setUpClass(cls):
        cls._speeches_path = os.path.abspath(speeches.__path__[0])

    def test_add_speech_fails_on_empty_form(self):
        # Test that the form won't submit if empty
        resp = self.client.post('/api/v0.1/speech/')
        self.assertEquals(resp.status_code, 400)
        self.assertEquals(resp['Content-Type'], 'application/json')
        response_content = simplejson.loads(resp.content)
        self.assertEquals(response_content['errors'], '{"__all__": ["You must provide either text or some audio"]}')

    def test_add_speech_without_speaker(self):
        # Test form without speaker
        resp = self.client.post('/api/v0.1/speech/', {
            'text': 'This is a speech'
        })
        self.assertEquals(resp.status_code, 201)
        self.assertEquals(resp['Content-Type'], 'application/json')
        self.assertEquals(resp['Location'], 'http://testserver/speech/1')
        # Check in db
        speech = Speech.objects.get(id=1)
        self.assertEqual(speech.text, 'This is a speech')