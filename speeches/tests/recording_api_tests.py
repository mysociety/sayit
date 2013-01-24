import os
import tempfile
import shutil
from datetime import datetime
import pytz

from django.test import TestCase
from django.test.utils import override_settings
from django.utils import simplejson
from django.conf import settings

import speeches
from speeches.models import Speech, Speaker, Recording, RecordingTimestamp

@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class RecordingAPITests(TestCase):

    @classmethod
    def setUpClass(cls):
        cls._in_fixtures = os.path.join(os.path.abspath(speeches.__path__[0]), 'fixtures', 'test_inputs')

    def tearDown(self):
        # Clear the recordings folder if it exists
        recordings_folder = os.path.join(settings.MEDIA_ROOT, 'recordings')
        if(os.path.exists(recordings_folder)):
            shutil.rmtree(recordings_folder)

    def test_add_recording_fails_on_empty_form(self):
        # Test that the form won't submit if empty
        resp = self.client.post('/api/v0.1/recording/')
        self.assertEquals(resp.status_code, 400)
        self.assertEquals(resp['Content-Type'], 'application/json')
        response_content = simplejson.loads(resp.content)
        self.assertEquals(response_content['errors'], '{"audio": ["This field is required."]}')

    def test_add_recording_with_audio(self):
        # Load the mp3 fixture
        audio = open(os.path.join(self._in_fixtures, 'lamb.mp3'), 'rb')

        resp = self.client.post('/api/v0.1/recording/', {
            'audio': audio
        })

        # Check response headers
        self.assertEquals(resp.status_code, 201)
        self.assertEquals(resp['Content-Type'], 'application/json')
        self.assertEquals(resp['Location'], 'http://testserver/recording/1')

        # Check response JSON
        response_content = simplejson.loads(resp.content)
        self.assertTrue(".mp3" in response_content['fields']['audio'])

        # Check in db
        recording = Recording.objects.get(id=1)
        self.assertIsNotNone(recording.audio)

    def test_add_recording_with_timestamp(self):
        # Add two speakers
        speaker = Speaker.objects.create(popit_url='http://popit.mysociety.org/api/v1/person/abcd', name='Steve')

        audio = open(os.path.join(self._in_fixtures, 'lamb.mp3'), 'rb')

        resp = self.client.post('/api/v0.1/recording/', {
            'audio': audio,
            'timestamps': '[{"speaker":"http://popit.mysociety.org/api/v1/person/abcd","timestamp":946684800000}]'
        })

        # Check response headers
        self.assertEquals(resp.status_code, 201)
        self.assertEquals(resp['Content-Type'], 'application/json')
        self.assertEquals(resp['Location'], 'http://testserver/recording/1')

        # Check response JSON
        response_content = simplejson.loads(resp.content)
        self.assertTrue(".mp3" in response_content['fields']['audio'])

        # Check in db
        recording = Recording.objects.get(id=1)
        self.assertIsNotNone(recording.audio)
        self.assertEquals(recording.timestamps.count(), 1)
        expected_timestamp = datetime.utcfromtimestamp(946684800).replace(tzinfo=pytz.utc)
        self.assertEquals(recording.timestamps.get(id=1).timestamp, expected_timestamp)

    def test_add_recording_with_multiple_timestamps(self):
        # Add two speakers
        speaker1 = Speaker.objects.create(popit_url='http://popit.mysociety.org/api/v1/person/abcd', name='Steve')
        speaker2 = Speaker.objects.create(popit_url='http://popit.mysociety.org/api/v1/person/efgh', name='Dave')
        speaker3 = Speaker.objects.create(popit_url='http://popit.mysociety.org/api/v1/person/hijk', name='Struan')

        audio = open(os.path.join(self._in_fixtures, 'lamb.mp3'), 'rb')

        timestamps = '[{"speaker":"http://popit.mysociety.org/api/v1/person/abcd","timestamp":946684800000},'
        timestamps += '{"speaker":"http://popit.mysociety.org/api/v1/person/efgh","timestamp":946684803000},'
        timestamps += '{"speaker":"http://popit.mysociety.org/api/v1/person/hijk","timestamp":946684804000}]'

        expected_timestamp1 = datetime.utcfromtimestamp(946684800).replace(tzinfo=pytz.utc)
        expected_timestamp2 = datetime.utcfromtimestamp(946684803).replace(tzinfo=pytz.utc)
        expected_timestamp3 = datetime.utcfromtimestamp(946684804).replace(tzinfo=pytz.utc)

        resp = self.client.post('/api/v0.1/recording/', {
            'audio': audio,
            'timestamps': timestamps
        })

        # Check response headers
        self.assertEquals(resp.status_code, 201)
        self.assertEquals(resp['Content-Type'], 'application/json')
        self.assertEquals(resp['Location'], 'http://testserver/recording/1')

        # Check response JSON
        response_content = simplejson.loads(resp.content)
        self.assertTrue(".mp3" in response_content['fields']['audio'])

        # Check in db
        # Check the recording
        recording = Recording.objects.get(id=1)
        self.assertIsNotNone(recording.audio)
        # Check the timestamps
        self.assertEquals(recording.timestamps.count(), 3)
        ordered_timestamps = recording.timestamps.order_by("timestamp")
        self.assertEquals(ordered_timestamps[0].timestamp, expected_timestamp1)
        self.assertEquals(ordered_timestamps[1].timestamp, expected_timestamp2)
        self.assertEquals(ordered_timestamps[2].timestamp, expected_timestamp3)
        # Check that speeches were made
        self.assertEquals(Speech.objects.count(), 3)

    def test_add_recording_with_unknown_speaker_timestamp(self):
        audio = open(os.path.join(self._in_fixtures, 'lamb.mp3'), 'rb')

        expected_timestamp = datetime.utcfromtimestamp(946684800).replace(tzinfo=pytz.utc)

        resp = self.client.post('/api/v0.1/recording/', {
            'audio': audio,
            'timestamps': '[{"speaker":"", "timestamp":946684800000}]'
        })

        # Check response headers
        self.assertEquals(resp.status_code, 201)
        self.assertEquals(resp['Content-Type'], 'application/json')
        self.assertEquals(resp['Location'], 'http://testserver/recording/1')

        # Check response JSON
        response_content = simplejson.loads(resp.content)
        self.assertTrue(".mp3" in response_content['fields']['audio'])

        # Check in db
        recording = Recording.objects.get(id=1)
        self.assertIsNotNone(recording.audio)
        self.assertEquals(recording.timestamps.all().count(), 1)
        self.assertEquals(recording.timestamps.get(id=1).timestamp, expected_timestamp)

    def test_add_recording_fails_with_unsupported_audio(self):
        # Load the .aiff fixture
        audio = open(os.path.join(self._in_fixtures, 'lamb.aiff'), 'rb')

        resp = self.client.post('/api/v0.1/recording/', {
            'audio': audio
        })

        # Assert that it fails and gives us an error
        self.assertEquals(resp.status_code, 400)
        self.assertEquals(resp['Content-Type'], 'application/json')
        response_content = simplejson.loads(resp.content)
        response_errors = simplejson.loads(response_content['errors'])
        self.assertEquals(response_errors['audio'], ["That file does not appear to be an audio file"])
