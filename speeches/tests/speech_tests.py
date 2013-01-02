import os
import tempfile
import shutil

from django.test import TestCase
from django.test.utils import override_settings
from django.conf import settings

import speeches
from speeches.models import Speech, Speaker

@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class SpeechTests(TestCase):

    @classmethod
    def setUpClass(cls):
        cls._speeches_path = os.path.abspath(speeches.__path__[0])

    def tearDown(self):
        # Clear the speeches folder if it exists
        speeches_folder = os.path.join(settings.MEDIA_ROOT, 'speeches')
        if(os.path.exists(speeches_folder)):
            shutil.rmtree(speeches_folder)

    def test_add_speech_page_exists(self):
        # Test that the page exists and has the right title
        resp = self.client.get('/speech/add')
        self.assertEqual(resp.status_code, 200)
        self.assertTrue('add a new speech' in resp.content)

    def test_add_speech_fails_on_empty_form(self):
        # Test that the form won't submit if empty
        resp = self.client.post('/speech/add')
        self.assertFormError(resp, 'form', None, 'You must provide either text or some audio')

    def test_add_speech_without_speaker(self):
        # Test form without speaker
        resp = self.client.post('/speech/add', {
            'text': 'This is a speech'
        })
        self.assertRedirects(resp, '/speech/1')
        # Check in db
        speech = Speech.objects.get(id=1)
        self.assertEqual(speech.text, 'This is a speech')

    def test_add_speech_with_speaker(self):
        # Test form with speaker, we need to add a speaker first
        speaker = Speaker.objects.create(popit_url='http://popit.mysociety.org/api/v1/person/abcd', name='Steve')

        resp = self.client.post('/speech/add', {
            'text': 'This is a Steve speech',
            'speaker': speaker.id
        })
        # Check in db
        speech = Speech.objects.get(speaker=speaker.id)
        self.assertEqual(speech.text, 'This is a Steve speech')

    def test_add_speech_with_audio(self):
        # Load the mp3 fixture
        audio = open(os.path.join(self._speeches_path, 'fixtures', 'lamb.mp3'), 'rb')

        resp = self.client.post('/speech/add', {
            'audio': audio
        })
        # Assert that it uploads and we're told to wait
        resp = self.client.get('/speech/1')
        self.assertTrue('Please wait' in resp.content)

        # Assert that it's in the model
        speech = Speech.objects.get(id=1)
        self.assertIsNotNone(speech.audio)

    def test_add_speech_with_audio_and_text(self):
        # Load the mp3 fixture
        audio = open(os.path.join(self._speeches_path, 'fixtures', 'lamb.mp3'), 'rb')
        text = 'This is a speech with some text'

        resp = self.client.post('/speech/add', {
            'audio': audio,
            'text': text
        })

        # Assert that it uploads and we see it straightaway
        resp = self.client.get('/speech/1')
        self.assertFalse('Please wait' in resp.content)        
        self.assertTrue(text in resp.content)

    def test_add_speech_fails_with_unsupported_audio(self):
        # Load the .aiff fixture
        audio = open(os.path.join(self._speeches_path, 'fixtures', 'lamb.aiff'), 'rb')

        resp = self.client.post('/speech/add', {
            'audio': audio
        })

        # Assert that it fails and gives us an error
        self.assertFormError(resp, 'form', 'audio', 'That file does not appear to be an audio file')

    def test_add_speech_creates_celery_task(self):
        # Load the mp3 fixture
        audio = open(os.path.join(self._speeches_path, 'fixtures', 'lamb.mp3'), 'rb')
        resp = self.client.post('/speech/add', {
            'audio': audio
        })

        # Assert that a celery task id is in the model
        speech = Speech.objects.get(id=1)
        self.assertIsNotNone(speech.celery_task_id)

    def test_add_speech_with_text_does_not_create_celery_task(self):
        # Load the mp3 fixture
        audio = open(os.path.join(self._speeches_path, 'fixtures', 'lamb.mp3'), 'rb')
        text = 'This is a speech with some text'

        resp = self.client.post('/speech/add', {
            'audio': audio,
            'text': text
        })

        # Assert that a celery task id is in the model
        speech = Speech.objects.get(id=1)
        self.assertIsNone(speech.celery_task_id)

    def test_speech_displayed_when_celery_task_finished(self):
        # Load the mp3 fixture
        audio = open(os.path.join(self._speeches_path, 'fixtures', 'lamb.mp3'), 'rb')
        text = 'This is a speech with some text'

        resp = self.client.post('/speech/add', {
            'audio': audio
        })

        # Assert that a celery task id is in the model
        speech = Speech.objects.get(id=1)
        self.assertIsNotNone(speech.celery_task_id)

        # Remove the celery task
        speech.celery_task_id = None
        speech.text = text
        speech.save()

        # Check the page doesn't show "Please wait" but shows our text instead
        resp = self.client.get('/speech/1')
        self.assertFalse('Please wait' in resp.content)        
        self.assertTrue(text in resp.content)