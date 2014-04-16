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
from speeches.utils import AudioHelper
from speeches.tests import InstanceTestCase

import logging
logging.disable(logging.WARNING)

@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class RecordingTimestampTests(InstanceTestCase):

    # TODO refactor with RecordingAPITests
    @classmethod
    def setUpClass(cls):
        cls._in_fixtures = os.path.join(os.path.abspath(speeches.__path__[0]), 'fixtures', 'test_inputs')

    def tearDown(self):
        # Clear the recordings folder if it exists
        recordings_folder = os.path.join(settings.MEDIA_ROOT, 'recordings')
        if(os.path.exists(recordings_folder)):
            shutil.rmtree(recordings_folder)

    def test_modify_timestamps(self, filename='lamb.mp3'):
        audio = open(os.path.join(self._in_fixtures, filename), 'rb')

        SPEECHES = 3
        # NOTE: this test is loosely cargo-culted from recording_api_tests,
        # however here timestamps are hardcoded for simplicity
        resp = self.client.post('/api/v0.1/recording/', {
            'audio': audio,
            'timestamps': '[{"timestamp":0},{"timestamp":2000},{"timestamp":4000}]'
        })

        def check_response(resp, expected_code=201, expected_type='application/json'):
            recording = Recording.objects.order_by('-id')[0]
            # Check response headers
            self.assertEquals(resp.status_code, expected_code)
            self.assertEquals(resp['Content-Type'], expected_type)
            self.assertIn('/recording/%d' % recording.id, resp['Location'])
            return recording

        recording = check_response(resp)
        timestamps = recording.timestamps.all()

        # Check the right number of timestamps and speeches were made
        self.assertEquals(recording.timestamps.count(), SPEECHES)
        self.assertEquals(Speech.objects.count(), SPEECHES)

        def check_audio_durations(recording, durations):
            audio_helper = AudioHelper()
            for (rt, d) in zip(recording.timestamps.all(), durations):
                self.assertEquals( 
                    audio_helper.get_audio_duration(rt.speech.audio.path),
                    d)

        check_audio_durations(recording, [2,2,1])

        form_data = {
            'timestamps-TOTAL_FORMS': 4,
            'timestamps-INITIAL_FORMS': 3,
            'timestamps-MAX_NUM_FORMS': 1000,
            'timestamps-0-recording': recording.id,
            'timestamps-0-id': timestamps[0].id,
            'timestamps-0-speaker': "",
            'timestamps-0-timestamp': 0,
            'timestamps-1-recording': recording.id,
            'timestamps-1-id': timestamps[1].id,
            'timestamps-1-speaker': "",
            'timestamps-1-timestamp': 3,
            'timestamps-2-recording': recording.id,
            'timestamps-2-id': timestamps[2].id,
            'timestamps-2-speaker': "",
            'timestamps-2-timestamp': 4,
            'timestamps-3-recording': recording.id,
            'timestamps-3-id': "",
            'timestamps-3-speaker': "",
            'timestamps-3-timestamp': "",
        }
        timestamps_2_id = timestamps[2].id
        resp = self.client.post('/recording/%d/edit' % recording.id,
            form_data)
        recording = check_response(resp, 302, 'text/html; charset=utf-8')
        check_audio_durations(recording, [3,1,1])

        form_data['timestamps-1-DELETE'] = 'on'
        resp = self.client.post('/recording/%d/edit' % recording.id,
            form_data)
        recording = check_response(resp, 302, 'text/html; charset=utf-8')
        check_audio_durations(recording, [4,1])

        form_data = {
            'timestamps-TOTAL_FORMS': 2,
            'timestamps-INITIAL_FORMS': 2,
            'timestamps-MAX_NUM_FORMS': 1000,
            'timestamps-0-DELETE': 'on',
            'timestamps-0-recording': recording.id,
            'timestamps-0-id': timestamps[0].id,
            'timestamps-0-speaker': "",
            'timestamps-0-timestamp': 0,
            'timestamps-1-recording': recording.id,
            'timestamps-1-id': timestamps_2_id,
            'timestamps-1-speaker': "",
            'timestamps-1-timestamp': 1,
        }
        resp = self.client.post('/recording/%d/edit' % recording.id,
            form_data)
        recording = check_response(resp, 302, 'text/html; charset=utf-8')
        check_audio_durations(recording, [4])

        # test new timestamp AFTER
        form_data = {
            'timestamps-TOTAL_FORMS': 2,
            'timestamps-INITIAL_FORMS': 1,
            'timestamps-MAX_NUM_FORMS': 1000,
            'timestamps-0-recording': recording.id,
            'timestamps-0-id': timestamps_2_id,
            'timestamps-0-speaker': "",
            'timestamps-0-timestamp': 1,
            'timestamps-1-recording': recording.id,
            'timestamps-1-id': '',
            'timestamps-1-speaker': "",
            'timestamps-1-timestamp': 4,
        }
        resp = self.client.post('/recording/%d/edit' % recording.id,
            form_data)
        recording = check_response(resp, 302, 'text/html; charset=utf-8')
        check_audio_durations(recording, [3,1])

        # test new timestamp BETWEEN
        form_data = {
            'timestamps-TOTAL_FORMS': 3,
            'timestamps-INITIAL_FORMS': 2,
            'timestamps-MAX_NUM_FORMS': 1000,
            'timestamps-0-recording': recording.id,
            'timestamps-0-id': timestamps_2_id,
            'timestamps-0-speaker': "",
            'timestamps-0-timestamp': 1,
            'timestamps-1-recording': recording.id,
            'timestamps-1-id': recording.timestamps.all()[1].id,
            'timestamps-1-speaker': "",
            'timestamps-1-timestamp': 4,
            'timestamps-2-recording': recording.id,
            'timestamps-2-id': '',
            'timestamps-2-speaker': "",
            'timestamps-2-timestamp': 3,
        }
        resp = self.client.post('/recording/%d/edit' % recording.id,
            form_data)
        recording = check_response(resp, 302, 'text/html; charset=utf-8')
        check_audio_durations(recording, [2,1,1])

        # test new timestamp BEFORE
        form_data = {
            'timestamps-TOTAL_FORMS': 4,
            'timestamps-INITIAL_FORMS': 3,
            'timestamps-MAX_NUM_FORMS': 1000,
            'timestamps-0-recording': recording.id,
            'timestamps-0-id': timestamps_2_id,
            'timestamps-0-speaker': "",
            'timestamps-0-timestamp': 1,
            'timestamps-1-recording': recording.id,
            'timestamps-1-id': recording.timestamps.all()[1].id,
            'timestamps-1-speaker': "",
            'timestamps-1-timestamp': 3,
            'timestamps-2-recording': recording.id,
            'timestamps-2-id': recording.timestamps.all()[2].id,
            'timestamps-2-speaker': "",
            'timestamps-2-timestamp': 4,
            'timestamps-3-recording': recording.id,
            'timestamps-3-id': '',
            'timestamps-3-speaker': "",
            'timestamps-3-timestamp': 0,
        }
        resp = self.client.post('/recording/%d/edit' % recording.id,
            form_data)
        recording = check_response(resp, 302, 'text/html; charset=utf-8')
        check_audio_durations(recording, [1,2,1,1])

    def test_can_get_form(self, filename='lamb.mp3'):
        audio = open(os.path.join(self._in_fixtures, filename), 'rb')

        # NOTE: this test is loosely cargo-culted from recording_api_tests,
        # however here timestamps are hardcoded for simplicity
        resp = self.client.post('/api/v0.1/recording/', {
            'audio': audio,
            'timestamps': '[{"timestamp":0},{"timestamp":2000},{"timestamp":4000}]'
        })

        recording = Recording.objects.order_by('-id')[0]
        self.assertEquals(resp.status_code, 201)

        resp = self.client.get('/recording/%d/edit' % recording.id)
        self.assertEquals(resp.status_code, 200)

    def test_change_speaker(self, filename='lamb.mp3'):
        audio = open(os.path.join(self._in_fixtures, filename), 'rb')

        # NOTE: this test is loosely cargo-culted from recording_api_tests,
        # however here timestamps are hardcoded for simplicity
        resp = self.client.post('/api/v0.1/recording/', {
            'audio': audio,
            'timestamps': '[{"timestamp":0},{"timestamp":2000},{"timestamp":4000}]'
        })

        recording = Recording.objects.order_by('-id')[0]
        self.assertEquals(resp.status_code, 201)

        resp = self.client.get('/recording/%d/edit' % recording.id)
        self.assertEquals(resp.status_code, 200)

        speaker_1 = Speaker.objects.create(name='Steve', instance=self.instance)
        speaker_2 = Speaker.objects.create(name='Yasmin', instance=self.instance)

        timestamps = recording.timestamps.all()
        
        form_data = {
            'timestamps-TOTAL_FORMS': 2,
            'timestamps-INITIAL_FORMS': 2,
            'timestamps-MAX_NUM_FORMS': 1000,
            'timestamps-0-recording': recording.id,
            'timestamps-0-id': timestamps[0].id,
            'timestamps-0-speaker': speaker_1.id,
            'timestamps-0-timestamp': 0,
            'timestamps-1-recording': recording.id,
            'timestamps-1-id': timestamps[1].id,
            'timestamps-1-speaker': speaker_2.id,
            'timestamps-1-timestamp': 1,
        }
        resp = self.client.post('/recording/%d/edit' % recording.id,
            form_data)
        recording = Recording.objects.order_by('-id')[0]

        timestamps = recording.timestamps.all()
        self.assertEquals(timestamps[0].speaker, speaker_1)
        self.assertEquals(timestamps[1].speaker, speaker_2)
