import os
import tempfile
import shutil

from django.test import TestCase
from django.test.utils import override_settings
from django.utils import simplejson
from django.conf import settings

import speeches
from speeches.models import Speaker, Recording, RecordingTimestamp

@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class RecordingAPITests(TestCase):

    @classmethod
    def setUpClass(cls):
        cls._speeches_path = os.path.abspath(speeches.__path__[0])

    def tearDown(self):
        # Clear the speeches folder if it exists
        speeches_folder = os.path.join(settings.MEDIA_ROOT, 'speeches')
        if(os.path.exists(speeches_folder)):
            shutil.rmtree(speeches_folder)

    def test_add_recording_fails_on_empty_form(self):
        # Test that the form won't submit if empty
        resp = self.client.post('/api/v0.1/recording/')
        self.assertEquals(resp.status_code, 400)
        self.assertEquals(resp['Content-Type'], 'application/json')
        response_content = simplejson.loads(resp.content)
        self.assertEquals(response_content['errors'], '{"audio": ["This field is required."]}')

    def test_add_recording_with_audio(self):
        # Load the mp3 fixture
        audio = open(os.path.join(self._speeches_path, 'fixtures', 'lamb.mp3'), 'rb')

        resp = self.client.post('/api/v0.1/recording/', {
            'audio': audio
        })

        # Check response headers
        self.assertEquals(resp.status_code, 201)
        self.assertEquals(resp['Content-Type'], 'application/json')
        self.assertEquals(resp['Location'], 'http://testserver/recording/1')

        # Check response JSON
        response_content = simplejson.loads(resp.content)
        self.assertTrue("lamb.mp3" in response_content['fields']['audio'])

        # Check in db
        recording = Recording.objects.get(id=1)
        self.assertIsNotNone(recording.audio)

    # def test_add_speech_fails_with_unsupported_audio(self):
    #     # Load the .aiff fixture
    #     audio = open(os.path.join(self._speeches_path, 'fixtures', 'lamb.aiff'), 'rb')

    #     resp = self.client.post('/api/v0.1/speech/', {
    #         'audio': audio
    #     })

    #     # Assert that it fails and gives us an error
    #     self.assertEquals(resp.status_code, 400)
    #     self.assertEquals(resp['Content-Type'], 'application/json')
    #     response_content = simplejson.loads(resp.content)
    #     response_errors = simplejson.loads(response_content['errors'])
    #     self.assertEquals(response_errors['audio'], ["That file does not appear to be an audio file"])
