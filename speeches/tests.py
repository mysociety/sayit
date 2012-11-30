"""
Testing of the speeches app.
Testing documentation is at https://docs.djangoproject.com/en/1.4/topics/testing/
"""

import os

from mock import patch

from selenium import webdriver

from requests import Response

from django.test import TestCase, LiveServerTestCase
from django.core.files import File
from django.conf import settings

import speeches
from speeches.models import Speech, Speaker
from speeches.tasks import transcribe_speech

class SpeechTest(TestCase):

    @classmethod
    def setUpClass(cls):
        cls._speeches_path = os.path.abspath(speeches.__path__[0])

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
        speaker = Speaker.objects.create(popit_id='abcd', name='Steve')

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

class TranscribeTaskTests(TestCase):

    @classmethod
    def setUpClass(cls):
        cls._speeches_path = os.path.abspath(speeches.__path__[0])
        # Tell Celery to be "eager", ie: run tasks straight away
        # as if they were normal methods
        if hasattr(settings, 'CELERY_ALWAYS_EAGER'):
            cls._OLD_CELERY_ALWAYS_EAGER = settings.CELERY_ALWAYS_EAGER
        settings.CELERY_ALWAYS_EAGER = True

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, '_OLD_CELERY_ALWAYS_EAGER'):
            settings.CELERY_ALWAYS_EAGER = cls._OLD_CELERY_ALWAYS_EAGER

    def setUp(self):
        # Put a speech in the db for the task to use
        audio = open(os.path.join(self._speeches_path, 'fixtures', 'lamb.mp3'), 'rb')
        self.speech = Speech.objects.create(audio=File(audio, "lamb.mp3"))

    def tearDown(self):
        self.speech.delete()

    @patch('requests.post')
    def test_happy_path(self, patched_post):
        # Test data
        auth_response = Response(
            status_code=200,
            json={
                'access_token': 'bb2da510a68542df9e4051cd9ebb0a5a',
                'expires_in': '0',
                'refresh_token': 'a096a765c27ff1ef7a0379d387769d603e6ad6c0'
            }
        )
        transcription = 'A transcription'
        transcription_response = Response(
            status_code=200,
            json={
                'Recognition': {
                    'Status': 'OK',
                    'ResponseId': 'c77727642111312f5cce0115a2ba8ce4',
                    'NBest': [
                        {   
                            'WordScores': [0.07, 0.1],
                            'Confidence': 0.601629956,
                            'Grade': 'accept',
                            'ResultText': transcription,
                            'Words': transcription.split(),
                            'LanguageId': 'en-US',
                            'Hypothesis': transcription
                        }
                    ]
                }
            }
        )

        # Setup the return values for our patched post method
        def return_side_effect(*args, **kwargs):
            if(args[0] == settings.ATT_OAUTH_URL):
                return auth_response
            elif(args[0] == settings.ATT_API_URL):
                return transcription_response        
        
        # Call our task to transcribe our file
        with patch(requests, 'post') as patched_post:
            patched_post.side_effect = return_side_effect
            result = transcribe_speech(self.speech.id)

        self.assertTrue(result.successful())

        # Assert that it saved the right data into the db
        self.assertTrue(transcription in speech.text)
        self.assertTrue(speech.celery_task_id is None)

    def test_speech_validation(self):
        self.fail()

    def test_wav_file_creation(self):
        self.fail()

    def test_always_deletes_tmp_file(self):
        self.fail()

    def test_auth_retrieval(self):
        self.fail()

    def test_api_call(self):
        self.fail()

    def test_transcription_selection(self):
        self.fail()

    def test_always_clears_task_on_error(self):
        self.fail()

class PopulateSpeakerCommandTests(TestCase):

    def test_populates_empty_db(self):
        self.fail()

    def test_updates_existing_records(self):
        self.fail()


class SeleniumTests(LiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        cls.selenium = webdriver.Firefox()
        super(SeleniumTests, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super(SeleniumTests, cls).tearDownClass()

    def test_add_speech(self):
        self.selenium.get('%s%s' % (self.live_server_url, '/speech/add'))
        text_input = self.selenium.find_element_by_name('text')
        text_input.send_keys('This is a speech')
        self.selenium.find_element_by_xpath('//input[@value="Add speech"]').click()
        self.assertIn('/speech/1', self.selenium.current_url)

    # TODO - test the ajax uploading

    # TODO - test the ajax autocomplete

