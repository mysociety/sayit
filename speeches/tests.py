"""
Testing of the speeches app.
Testing documentation is at https://docs.djangoproject.com/en/1.4/topics/testing/
"""

import os
import tempfile
import filecmp

from mock import patch, Mock

from selenium import webdriver

import requests

from popit import PopIt

from django.test import TestCase, LiveServerTestCase
from django.core.files import File
from django.core import management
from django.conf import settings

import speeches
from speeches.models import Speech, Speaker
from speeches.tasks import transcribe_speech, TranscribeHelper, TranscribeException

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
        # Undo the celery settings we changed, just in case
        if hasattr(cls, '_OLD_CELERY_ALWAYS_EAGER'):
            settings.CELERY_ALWAYS_EAGER = cls._OLD_CELERY_ALWAYS_EAGER
        else:
            del settings.CELERY_ALWAYS_EAGER

    def setUp(self):
        # Put a speech in the db for the task to use
        audio = open(os.path.join(self._speeches_path, 'fixtures', 'lamb.mp3'), 'rb')
        self.speech = Speech.objects.create(audio=File(audio, "lamb.mp3"))

    def tearDown(self):
        self.speech.delete()

    def test_happy_path(self):
        # Canned responses for our code to use
        attrs = {
            'status_code': 200,
            'json': { 
                "access_token": "bb2da510a68542df9e4051cd9ebb0a5a", 
                "expires_in": "0", 
                "refresh_token": "a096a765c27ff1ef7a0379d387769d603e6ad6c0" 
            }
        }
        auth_response = Mock(spec=requests.Response, **attrs)
        
        transcription = 'A transcription'
        attrs = { 
            'status_code': 200,
            'json': { 
                "Recognition": { 
                    "Status": "OK", 
                    "ResponseId": "c77727642111312f5cce0115a2ba8ce4", 
                    "NBest": [ { 
                        "WordScores": [0.07, 0.1], 
                        "Confidence": 0.601629956,
                        "Grade": "accept", 
                        "ResultText": transcription, 
                        "Words": ["A", "transcription"], 
                        "LanguageId": "en-US", 
                        "Hypothesis": transcription 
                    } ]
                }
            }
        }
        transcription_response = Mock(spec=requests.Response, **attrs)

        # Setup the return values for our patched post method
        def return_side_effect(*args, **kwargs):
            if(args[0] == settings.ATT_OAUTH_URL):
                return auth_response
            elif(args[0] == settings.ATT_API_URL):
                return transcription_response        
        
        # Call our task to transcribe our file
        with patch('requests.post') as patched_post:
            patched_post.side_effect = return_side_effect
            result = transcribe_speech(self.speech.id)

        # Assert that it saved the right data into the db
        self.speech = Speech.objects.get(id=self.speech.id)
        self.assertTrue(transcription in self.speech.text)
        self.assertTrue(self.speech.celery_task_id is None)

    def test_speech_validation(self):
        helper = TranscribeHelper()

        # Valid speech should be ok
        helper.check_speech(self.speech)

        # Speech with no audio should error
        speech_no_audio = Speech.objects.create(audio=None)
        with self.assertRaises(TranscribeException):
            helper.check_speech(speech_no_audio)

        # Speech with text should error
        speech_has_text = Speech.objects.create(text="Text")
        with self.assertRaises(TranscribeException):
            helper.check_speech(speech_has_text)


    def test_wav_file_creation(self):
        helper = TranscribeHelper()
        
        (fd, tmp_filename) = tempfile.mkstemp(suffix='.wav')
        helper.make_wav(tmp_filename, self.speech.audio.path)

        # Compare the created file to one we made earlier
        self.assertTrue(filecmp.cmp(tmp_filename, os.path.join(self._speeches_path, 'fixtures', 'lamb.wav')))

    def test_transcription_selection(self):
        # Mock responses

        # Single acceptable response (happy path)
        accept_transcription_response = { 
            "Recognition": { 
                "Status": "OK", 
                "ResponseId": "c77727642111312f5cce0115a2ba8ce4", 
                "NBest": [ { 
                    "WordScores": [0.07, 0.1], 
                    "Confidence": 0.601629956,
                    "Grade": "accept", 
                    "ResultText": 'A transcription', 
                    "Words": ["A", "transcription"], 
                    "LanguageId": "en-US", 
                    "Hypothesis": 'A transcription' 
                } ]
            }
        }

        # "Confirm" grade response - should be accepted too
        confirm_transcription_response = { 
            "Recognition": { 
                "Status": "OK", 
                "ResponseId": "c77727642111312f5cce0115a2ba8ce4", 
                "NBest": [ { 
                    "WordScores": [0.07, 0.1], 
                    "Confidence": 0.3,
                    "Grade": "confirm", 
                    "ResultText": 'A transcription', 
                    "Words": ["A", "transcription"], 
                    "LanguageId": "en-US", 
                    "Hypothesis": 'A transcription' 
                } ]
            }
        }

        # Reject response - should be rejected
        reject_transcription_response = { 
            "Recognition": { 
                "Status": "OK", 
                "ResponseId": "c77727642111312f5cce0115a2ba8ce4", 
                "NBest": [ { 
                    "WordScores": [0.07, 0.1], 
                    "Confidence": 0.0,
                    "Grade": "reject", 
                    "ResultText": 'A transcription', 
                    "Words": ["A", "transcription"], 
                    "LanguageId": "en-US", 
                    "Hypothesis": 'A transcription' 
                } ]
            }
        }

        # Multiple acceptable responses - should pick the one with the highest confidence
        multiple_transcription_response = {  
            "Recognition": { 
                "Status": "OK", 
                "ResponseId": "c77727642111312f5cce0115a2ba8ce4", 
                "NBest": [ 
                    { 
                        "WordScores": [0.07, 0.1], 
                        "Confidence": 0.9,
                        "Grade": "accept", 
                        "ResultText": 'Best transcription', 
                        "Words": ["Best", "transcription"], 
                        "LanguageId": "en-US", 
                        "Hypothesis": 'Best transcription' 
                    },
                    { 
                        "WordScores": [0.07, 0.1], 
                        "Confidence": 0.8,
                        "Grade": "accept", 
                        "ResultText": 'A transcription', 
                        "Words": ["A", "transcription"], 
                        "LanguageId": "en-US", 
                        "Hypothesis": 'A transcription' 
                    }
                ]
            }
        }

        helper = TranscribeHelper()

        self.assertTrue(helper.best_transcription(accept_transcription_response) == "A transcription")
        self.assertTrue(helper.best_transcription(confirm_transcription_response) == "A transcription")
        self.assertTrue(helper.best_transcription(reject_transcription_response) is None)
        self.assertTrue(helper.best_transcription(multiple_transcription_response) == "Best transcription")
        
    # There are numerous places where we could error:
    # checking a speech
    # making a temp file
    # making a wav file
    # getting an auth token
    # getting a transcription
    # removing the temp file
    # So we test with a mock that throws an Exception at each of these in turn
    def test_clears_task_on_valid_speech_error(self):
        with patch('speeches.tasks.TranscribeHelper.check_speech') as patched_helper:
            patched_helper.side_effect = Exception("Boom!")
            with self.assertRaises(Exception):
                result = transcribe_speech(self.speech.id)

        # Assert that it saved the right data into the db
        speech = Speech.objects.get(id=self.speech.id)
        self.assertTrue(speech.celery_task_id is None)

    def test_clears_task_on_temp_file_errors(self):
        with patch('tempfile.mkstemp') as patched_mkstemp:
            patched_mkstemp.side_effect = Exception("Boom!")
            with self.assertRaises(Exception):
                result = transcribe_speech(self.speech.id)

        # Assert that it saved the right data into the db
        speech = Speech.objects.get(id=self.speech.id)
        self.assertTrue(speech.celery_task_id is None)

    def test_clears_task_on_wav_file_errors(self):
        with patch('subprocess.call') as patched_call:
            patched_call.side_effect = Exception("Boom!")
            with self.assertRaises(Exception):
                result = transcribe_speech(self.speech.id)

        # Assert that it saved the right data into the db
        speech = Speech.objects.get(id=self.speech.id)
        self.assertTrue(speech.celery_task_id is None)

    def test_clears_task_on_auth_errors(self):
        with patch('speeches.tasks.TranscribeHelper.get_oauth_token') as patched_get_oauth_token:
            patched_get_oauth_token.side_effect = Exception("Boom!")
            with self.assertRaises(Exception):
                result = transcribe_speech(self.speech.id)

        # Assert that it saved the right data into the db
        speech = Speech.objects.get(id=self.speech.id)
        self.assertTrue(speech.celery_task_id is None)

    def test_clears_task_on_api_errors(self):
        with patch('speeches.tasks.TranscribeHelper.get_oauth_token') as patched_get_oauth_token:
            patched_get_oauth_token.return_value = "bb2da510a68542df9e4051cd9ebb0a5a"
            with patch('speeches.tasks.TranscribeHelper.get_transcription') as patched_get_transcription:
                patched_get_transcription.side_effect = Exception("Boom!")
                with self.assertRaises(Exception):
                    result = transcribe_speech(self.speech.id)

        # Assert that it saved the right data into the db
        speech = Speech.objects.get(id=self.speech.id)
        self.assertTrue(speech.celery_task_id is None)

    def test_clears_task_on_removing_tmp_file_errors(self):
        with patch('os.remove') as patched_remove:
            patched_remove.side_effect = Exception("Boom!")
            with self.assertRaises(Exception):
                result = transcribe_speech(self.speech.id)

        # Assert that it saved the right data into the db
        speech = Speech.objects.get(id=self.speech.id)
        self.assertTrue(speech.celery_task_id is None)


class PopulateSpeakerCommandTests(TestCase):

    def test_populates_empty_db(self):
        # Canned data to simulate a response from popit
        people = [
            {
                '_id': 'abcde',
                'name': 'Test 1'
            },
            {
                '_id': 'fghij',
                'name': 'Test 2'
            }
        ]
        # Mock out popit and then call our command
        popit_config = { 'person': Mock(), 'person.get.return_value': {'results': people} }
        with patch('speeches.management.commands.populatespeakers.PopIt', spec=PopIt, **popit_config) as patched_popit:
            management.call_command('populatespeakers')

        db_people = Speaker.objects.all()
        self.assertTrue(len(db_people) == 2)
        self.assertTrue(db_people[0].popit_id == 'abcde')
        self.assertTrue(db_people[0].name == 'Test 1')
        self.assertTrue(db_people[1].popit_id == 'fghij')
        self.assertTrue(db_people[1].name == 'Test 2')

    def test_updates_existing_records(self):
        # Add a record into the db first
        existing_person = Speaker.objects.create(popit_id="abcde", name="test 1")

        # Canned data to simulate a response from popit
        changed_people = [
            {
                '_id': 'abcde',
                'name': 'Test 3' # Note changed name
            },
            {
                '_id': 'fghij',
                'name': 'Test 2'
            }
        ]
        # Mock out popit and then call our command
        popit_config = { 'person': Mock(), 'person.get.return_value': {'results': changed_people} }
        with patch('speeches.management.commands.populatespeakers.PopIt', spec=PopIt, **popit_config) as new_patched_popit:
            management.call_command('populatespeakers')

        db_people = Speaker.objects.all()
        self.assertTrue(len(db_people) == 2)
        self.assertTrue(db_people[0].popit_id == 'abcde')
        self.assertTrue(db_people[0].name == 'Test 3')
        self.assertTrue(db_people[1].popit_id == 'fghij')
        self.assertTrue(db_people[1].name == 'Test 2')

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
