import logging
import os
import tempfile
import shutil
from datetime import datetime, timedelta
import pytz

from django.test.utils import override_settings
from django.conf import settings

import speeches
from speeches.models import Speech, Recording, Section
from speeches.tests import InstanceTestCase

logging.disable(logging.WARNING)


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class RecordingTests(InstanceTestCase):

    @classmethod
    def setUpClass(cls):
        cls._in_fixtures = os.path.join(os.path.abspath(speeches.__path__[0]), 'fixtures', 'test_inputs')
        super(RecordingTests, cls).setUpClass()

    def tearDown(self):
        # Clear the recordings folder if it exists
        recordings_folder = os.path.join(settings.MEDIA_ROOT, 'recordings')
        if(os.path.exists(recordings_folder)):
            shutil.rmtree(recordings_folder)

    def test_edit_recording_timestamps(self, filename='lamb.mp3'):
        # For now, just call the API to create the initial thing.
        # Probably should have some better way of doing this self-contained...
        SPEECHES = 4

        timestamps = '['
        for i in range(SPEECHES):
            t = 946684800 + i
            timestamps += '{"timestamp":' + str(t) + '000}'
            if i < SPEECHES - 1:
                timestamps += ','
        timestamps += ']'

        audio = open(os.path.join(self._in_fixtures, filename), 'rb')
        resp = self.client.post('/api/v0.1/recording/', {
            'audio': audio,
            'timestamps': timestamps
        })

        recording = Recording.objects.order_by('-id')[0]
        self.assertIsNotNone(recording.audio)
        self.assertEqual(recording.audio_duration, 5)
        expected_timestamp = datetime.utcfromtimestamp(946684800).replace(tzinfo=pytz.utc)
        self.assertEqual(recording.start_datetime, expected_timestamp)
        self.assertEqual(recording.timestamps.count(), SPEECHES)
        self.assertEqual(Speech.objects.count(), SPEECHES)

        # Test each speech is a second apart
        last_start = None
        for s in Speech.objects.all():
            start = datetime.combine(s.start_date, s.start_time)
            if last_start:
                self.assertEqual(start - last_start, timedelta(seconds=1))
            last_start = start

        # Test assignment of section
        section = Section.objects.create(heading='A Section', instance=self.instance)
        self.assertEqual(Speech.objects.filter(section=section).count(), 0)
        resp = self.client.get('/recording/%s' % recording.id)
        self.assertContains(resp, 'A Section')
        resp = self.client.post('/recording/%s' % recording.id, {'section': section.id})
        self.assertEqual(Speech.objects.filter(section=section).count(), SPEECHES)

        # XXX Perhaps django-webtest (which has form.submit()) or
        # get things out of the view and test them independently.
        args = {
            "timestamps-TOTAL_FORMS": 4,
            "timestamps-INITIAL_FORMS": 4,
        }
        new = [0, 1, 3, 4]
        for i in range(SPEECHES):
            args['timestamps-%d-id' % i] = recording.timestamps.all()[i].id
            args['timestamps-%d-recording' % i] = recording.id
            args['timestamps-%d-timestamp' % i] = new[i]
        resp = self.client.post('/recording/%s/edit' % recording.id, args)

        # Now test the speeches are differently spaced apart
        last_start = None
        diffs = [None, 1, 2, 1]
        for i, s in enumerate(Speech.objects.all()):
            start = datetime.combine(s.start_date, s.start_time)
            if last_start:
                self.assertEqual(start - last_start, timedelta(seconds=diffs[i]))
            last_start = start
