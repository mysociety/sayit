import os
import tempfile
import shutil
from datetime import datetime
import pytz

from django.test.utils import override_settings
from django.utils import simplejson
from django.conf import settings

from instances.tests import InstanceTestCase

import speeches
from speeches.models import Speech, Speaker, Recording, RecordingTimestamp
from speeches.tests.recording_api_tests import RecordingAPITests
from speeches.utils import AudioHelper

@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class RecordingTimestampTests(RecordingAPITests):

    def test_modify_timestamps(self, filename='lamb.mp3'):
        audio = open(os.path.join(self._in_fixtures, filename), 'rb')

        SPEECHES = 2
        # NOTE: this test is loosely cargo-culted from recording_api_tests,
        # however here timestamps are hardcoded for simplicity
        resp = self.client.post('/api/v0.1/recording/', {
            'audio': audio,
            'timestamps': '[{"timestamp":0},{"timestamp":3000}]'
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

        check_audio_durations(recording, [3,2])

        resp = self.client.post('/recording/%d/edit' % recording.id, {
            # csrfmiddlewaretoken ???
            'timestamps-TOTAL_FORMS': 2,
            'timestamps-INITIAL_FORMS': 2,
            'timestamps-MAX_NUM_FORMS': 1000,
            'timestamps-0-recording': recording.id,
            'timestamps-0-id': timestamps[0].id,
            'timestamps-0-speaker': "",
            'timestamps-0-timestamp': "1970-01-01 01:00:00",
            'timestamps-1-recording': recording.id,
            'timestamps-1-id': timestamps[1].id,
            'timestamps-1-speaker': "",
            'timestamps-1-timestamp': "1970-01-01 01:00:01", # 1 second
        })

        recording = check_response(resp, 302, 'text/html; charset=utf-8')

        check_audio_durations(recording, [1,4])
