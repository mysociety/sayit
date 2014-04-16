import os
import tempfile
import shutil
from datetime import datetime
import pytz

from django.test.utils import override_settings
from django.utils import simplejson
from django.conf import settings

import speeches
from speeches.models import Speech, Speaker, Recording, RecordingTimestamp
from speeches.tests import InstanceTestCase

@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class RecordingAPITests(InstanceTestCase):

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

        recording = Recording.objects.order_by('-id')[0]

        # Check response headers
        self.assertEquals(resp.status_code, 201)
        self.assertEquals(resp['Content-Type'], 'application/json')
        self.assertIn('/recording/%d' % recording.id, resp['Location'])

        # Check response JSON
        response_content = simplejson.loads(resp.content)
        self.assertTrue(".mp3" in response_content['fields']['audio'])

        # Check in db
        self.assertIsNotNone(recording.audio)
        self.assertEquals(recording.audio_duration, 5)

    def test_add_recording_with_timestamp(self):
        # Add two speakers
        speaker = Speaker.objects.create(name='Steve', instance=self.instance)

        audio = open(os.path.join(self._in_fixtures, 'lamb.mp3'), 'rb')

        resp = self.client.post('/api/v0.1/recording/', {
            'audio': audio,
            'timestamps': '[{"speaker":"1","timestamp":946684800000}]'
        })

        recording = Recording.objects.order_by('-id')[0]

        # Check response headers
        self.assertEquals(resp.status_code, 201)
        self.assertEquals(resp['Content-Type'], 'application/json')
        self.assertIn('/recording/%d' % recording.id, resp['Location'])

        # Check response JSON
        response_content = simplejson.loads(resp.content)
        self.assertTrue(".mp3" in response_content['fields']['audio'])

        # Check in db
        self.assertIsNotNone(recording.audio)
        self.assertEquals(recording.timestamps.count(), 1)
        expected_timestamp = datetime.utcfromtimestamp(946684800).replace(tzinfo=pytz.utc)
        self.assertEquals(recording.timestamps.all()[0].timestamp, expected_timestamp)
        self.assertEquals(recording.start_datetime, expected_timestamp)

    def test_add_ogg_with_multiple_timestamps(self):
        self.test_add_recording_with_multiple_timestamps('lamb.ogg')

    def test_add_recording_with_multiple_timestamps(self, filename='lamb.mp3'):
        SPEECHES = 3

        speakers = []
        expected_timestamps = []
        timestamps = '['
        for i in range(SPEECHES):
            s = Speaker.objects.create(name='Speaker ' + str(i), instance=self.instance)
            t = 946684800 + i*3
            speakers.append(s)
            expected_timestamps.append( datetime.utcfromtimestamp(t).replace(tzinfo=pytz.utc) )
            timestamps += '{"speaker":"' + str(s.id) + '","timestamp":' + str(t) + '000}'
            if i<SPEECHES-1:
                timestamps += ','
        timestamps += ']'

        audio = open(os.path.join(self._in_fixtures, filename), 'rb')
        resp = self.client.post('/api/v0.1/recording/', {
            'audio': audio,
            'timestamps': timestamps
        })

        recording = Recording.objects.order_by('-id')[0]

        # Check response headers
        self.assertEquals(resp.status_code, 201)
        self.assertEquals(resp['Content-Type'], 'application/json')
        self.assertIn('/recording/%d' % recording.id, resp['Location'])

        # Check response JSON
        response_content = simplejson.loads(resp.content)
        self.assertTrue(".mp3" in response_content['fields']['audio'])

        # Check in db
        # Check the recording
        self.assertIsNotNone(recording.audio)
        self.assertRegexpMatches(recording.audio.path, r'\.mp3$')

        # Check the right number of timestamps and speeches were made
        self.assertEquals(recording.timestamps.count(), SPEECHES)
        self.assertEquals(Speech.objects.count(), SPEECHES)

        # Check the timestamps and speeches are what we expect (ish)
        ordered_timestamps = recording.timestamps.order_by("timestamp")
        for i in range(SPEECHES):
            self.assertEquals(ordered_timestamps[i].timestamp, expected_timestamps[i])
            speech = Speech.objects.all()[i]
            self.assertEquals(speech.speaker, speakers[i])
            self.assertEquals(speech.start_date, expected_timestamps[i].date())
            self.assertEquals(speech.start_time, expected_timestamps[i].time())
            if i==SPEECHES-1:
                self.assertEquals(speech.end_date, None)
                self.assertEquals(speech.end_time, None)
            else:
                self.assertEquals(speech.end_date, expected_timestamps[i+1].date())
                self.assertEquals(speech.end_time, expected_timestamps[i+1].time())
            self.assertIsNotNone(speech.audio.path)
            self.assertRegexpMatches(speech.audio.path, r'\.mp3$')
            self.assertEquals(speech, ordered_timestamps[i].speech)

    def test_add_recording_with_unknown_speaker_timestamp(self):
        audio = open(os.path.join(self._in_fixtures, 'lamb.mp3'), 'rb')

        expected_timestamp = datetime.utcfromtimestamp(946684800).replace(tzinfo=pytz.utc)

        resp = self.client.post('/api/v0.1/recording/', {
            'audio': audio,
            'timestamps': '[{"speaker":"", "timestamp":946684800000}]'
        })

        recording = Recording.objects.order_by('-id')[0]

        # Check response headers
        self.assertEquals(resp.status_code, 201)
        self.assertEquals(resp['Content-Type'], 'application/json')
        self.assertIn('/recording/%d' % recording.id, resp['Location'])

        # Check response JSON
        response_content = simplejson.loads(resp.content)
        self.assertTrue(".mp3" in response_content['fields']['audio'])

        # Check in db
        self.assertIsNotNone(recording.audio)
        self.assertEquals(recording.timestamps.all().count(), 1)
        self.assertEquals(recording.timestamps.all()[0].timestamp, expected_timestamp)

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
