import os
import tempfile
import shutil

from django.test.utils import override_settings
from django.utils import simplejson
from django.conf import settings

from instances.tests import InstanceTestCase

import speeches
from speeches.models import Speech, Speaker

@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class SpeechAPITests(InstanceTestCase):

    @classmethod
    def setUpClass(cls):
        cls._in_fixtures = os.path.join(os.path.abspath(speeches.__path__[0]), 'fixtures', 'test_inputs')

    def tearDown(self):
        # Clear the speeches folder if it exists
        speeches_folder = os.path.join(settings.MEDIA_ROOT, 'speeches')
        if(os.path.exists(speeches_folder)):
            shutil.rmtree(speeches_folder)

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

        # Check response headers
        self.assertEquals(resp['Content-Type'], 'application/json')
        self.assertRedirects(resp, 'speech/1', status_code=201)

        # Check response JSON
        response_content = simplejson.loads(resp.content)
        self.assertEquals(response_content['fields']['text'], 'This is a speech')
        self.assertIsNone(response_content['fields']['speaker'])

        # Check in db
        speech = Speech.objects.get(id=1)
        self.assertEqual(speech.text, 'This is a speech')


    def test_add_speech_with_speaker(self):
        # Test form with speaker, we need to add a speaker first
        speaker = Speaker.objects.create(popit_url='http://popit.mysociety.org/api/v1/person/abcd', name='Steve', instance=self.instance)

        resp = self.client.post('/api/v0.1/speech/', {
            'text': 'This is a Steve speech',
            'speaker': speaker.popit_url
        })

        # Check response headers
        self.assertEquals(resp.status_code, 201)
        self.assertEquals(resp['Content-Type'], 'application/json')
        self.assertRedirects(resp, 'speech/1', status_code=201)

        # Check response JSON
        response_content = simplejson.loads(resp.content)
        self.assertEquals(response_content['fields']['text'], 'This is a Steve speech')
        self.assertEquals(response_content['fields']['speaker'], 1)

        # Check in db
        speech = Speech.objects.get(speaker=speaker.id)
        self.assertEqual(speech.text, 'This is a Steve speech')

    def test_add_speech_with_audio(self):
        # Load the mp3 fixture
        audio = open(os.path.join(self._in_fixtures, 'lamb.mp3'), 'rb')

        resp = self.client.post('/api/v0.1/speech/', {
            'audio': audio
        })

        # Check response headers
        self.assertEquals(resp['Content-Type'], 'application/json')
        self.assertRedirects(resp, 'speech/1', status_code=201)

        # Check response JSON
        response_content = simplejson.loads(resp.content)
        self.assertTrue(".mp3" in response_content['fields']['audio'])

        # Check in db
        speech = Speech.objects.get(id=1)
        self.assertIsNotNone(speech.audio)

    def test_add_speech_with_audio_and_text(self):
        # Load the mp3 fixture
        audio = open(os.path.join(self._in_fixtures, 'lamb.mp3'), 'rb')
        text = 'This is a speech with some text'

        resp = self.client.post('/api/v0.1/speech/', {
            'audio': audio,
            'text': text
        })

        # Check response headers
        self.assertEquals(resp['Content-Type'], 'application/json')
        self.assertRedirects(resp, 'speech/1', status_code=201)

        # Check response JSON
        response_content = simplejson.loads(resp.content)
        self.assertTrue(".mp3" in response_content['fields']['audio'])
        self.assertEquals(response_content['fields']['text'], text)

        # Check in db
        speech = Speech.objects.get(id=1)
        self.assertIsNotNone(speech.audio)

    def test_add_speech_fails_with_unsupported_audio(self):
        # Load the .aiff fixture
        audio = open(os.path.join(self._in_fixtures, 'lamb.aiff'), 'rb')

        resp = self.client.post('/api/v0.1/speech/', {
            'audio': audio
        })

        # Assert that it fails and gives us an error
        self.assertEquals(resp.status_code, 400)
        self.assertEquals(resp['Content-Type'], 'application/json')
        response_content = simplejson.loads(resp.content)
        response_errors = simplejson.loads(response_content['errors'])
        self.assertEquals(response_errors['audio'], ["That file does not appear to be an audio file"])

    def test_add_speech_creates_celery_task(self):
        # Load the mp3 fixture
        audio = open(os.path.join(self._in_fixtures, 'lamb.mp3'), 'rb')
        resp = self.client.post('/api/v0.1/speech/', {
            'audio': audio
        })

        # Assert that a celery task id is in the model
        speech = Speech.objects.get(id=1)
        self.assertIsNotNone(speech.celery_task_id)

    def test_add_speech_with_text_does_not_create_celery_task(self):
        # Load the mp3 fixture
        audio = open(os.path.join(self._in_fixtures, 'lamb.mp3'), 'rb')
        text = 'This is a speech with some text'

        resp = self.client.post('/api/v0.1/speech/', {
            'audio': audio,
            'text': text
        })

        # Assert that a celery task id is in the model
        speech = Speech.objects.get(id=1)
        self.assertIsNone(speech.celery_task_id)
