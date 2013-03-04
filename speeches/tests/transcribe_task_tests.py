import os
import tempfile
import shutil

from mock import patch, Mock

import requests

from django.test.utils import override_settings
from django.core.files import File
from django.conf import settings

from instances.tests import InstanceTestCase

import speeches
from speeches.models import Speech
from speeches.tasks import transcribe_speech
from speeches.utils import TranscribeHelper, TranscribeException

@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class TranscribeTaskTests(InstanceTestCase):

    @classmethod
    def setUpClass(cls):
        cls._in_fixtures = os.path.join(os.path.abspath(speeches.__path__[0]), 'fixtures', 'test_inputs')
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
        super(TranscribeTaskTests, self).setUp()
        audio = open(os.path.join(self._in_fixtures, 'lamb.mp3'), 'rb')
        self.speech = Speech.objects.create(audio=File(audio, "lamb.mp3"), instance=self.instance)

    def tearDown(self):
        self.speech.delete()
        # Clear the speeches folder if it exists
        speeches_folder = os.path.join(settings.MEDIA_ROOT, 'speeches')
        if(os.path.exists(speeches_folder)):
            shutil.rmtree(speeches_folder)

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
        speech_no_audio = Speech.objects.create(audio=None, instance=self.instance)
        with self.assertRaises(TranscribeException):
            helper.check_speech(speech_no_audio)

        # Speech with text should error
        speech_has_text = Speech.objects.create(text="Text", instance=self.instance)
        with self.assertRaises(TranscribeException):
            helper.check_speech(speech_has_text)

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
        with patch('speeches.utils.TranscribeHelper.check_speech') as patched_helper:
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
        with patch('speeches.utils.TranscribeHelper.get_oauth_token') as patched_get_oauth_token:
            patched_get_oauth_token.side_effect = Exception("Boom!")
            with self.assertRaises(Exception):
                result = transcribe_speech(self.speech.id)

        # Assert that it saved the right data into the db
        speech = Speech.objects.get(id=self.speech.id)
        self.assertTrue(speech.celery_task_id is None)

    def test_clears_task_on_api_errors(self):
        with patch('speeches.utils.TranscribeHelper.get_oauth_token') as patched_get_oauth_token:
            patched_get_oauth_token.return_value = "bb2da510a68542df9e4051cd9ebb0a5a"
            with patch('speeches.utils.TranscribeHelper.get_transcription') as patched_get_transcription:
                patched_get_transcription.side_effect = Exception("Boom!")
                with self.assertRaises(Exception):
                    result = transcribe_speech(self.speech.id)

        # Assert that it saved the right data into the db
        speech = Speech.objects.get(id=self.speech.id)
        self.assertTrue(speech.celery_task_id is None)

    def test_clears_task_on_removing_tmp_file_errors(self):
        with patch('speeches.utils.TranscribeHelper.get_oauth_token') as patched_get_oauth_token:
            patched_get_oauth_token.return_value = "bb2da510a68542df9e4051cd9ebb0a5a"
            with patch('speeches.utils.TranscribeHelper.get_transcription') as patched_get_transcription:
                patched_get_transcription.return_value = {
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
                with patch('os.remove') as patched_remove:
                    patched_remove.side_effect = Exception("Boom!")
                    with self.assertRaises(Exception):
                        result = transcribe_speech(self.speech.id)

        # Assert that it saved the right data into the db
        speech = Speech.objects.get(id=self.speech.id)
        self.assertTrue(speech.celery_task_id is None)
