import os
import tempfile
import filecmp
from datetime import timedelta

from django.test import TestCase
from django.core.files import File
from django.utils import timezone

import speeches
from speeches.utils import AudioHelper
from speeches.models import Recording, RecordingTimestamp, Speaker

class AudioHelperTests(TestCase):

    @classmethod
    def setUpClass(cls):
        cls._in_fixtures = os.path.join(os.path.abspath(speeches.__path__[0]), 'fixtures', 'test_inputs')
        cls._expected_fixtures = os.path.join(os.path.abspath(speeches.__path__[0]), 'fixtures', 'expected_outputs')

    def setUp(self):
        self.helper = AudioHelper()
        self.tmp_filename = None

    def tearDown(self):
        if self.tmp_filename is not None:
            os.remove(self.tmp_filename)

    def expected_output_file(self, filename):
        _, extension = os.path.splitext(filename)
        return os.path.join(self._expected_fixtures,
                            extension[1:],
                            filename)

    def test_wav_file_creation_from_mp3(self):
        self.tmp_filename = self.helper.make_wav(os.path.join(self._in_fixtures, 'lamb.mp3'))

        # Compare the created file to one we made earlier
        self.assertTrue(filecmp.cmp(self.tmp_filename, self.expected_output_file('lamb_from_mp3.wav')))

    def test_wav_file_creation_from_android_3gp(self):
        self.tmp_filename = self.helper.make_wav(os.path.join(self._in_fixtures, 'lamb.3gp'))

        # Compare the created file to one we made earlier
        self.assertTrue(filecmp.cmp(self.tmp_filename, self.expected_output_file('lamb_from_3gp.wav')))

    def test_wav_file_creation_from_iphone_wav(self):
        self.tmp_filename = self.helper.make_wav(os.path.join(self._in_fixtures, 'lamb_iphone.wav'))

        # Compare the created file to one we made earlier
        self.assertTrue(filecmp.cmp(self.tmp_filename, self.expected_output_file('lamb_from_iphone.wav')))

    def test_wav_file_creation_from_stereo_wav(self):
        self.tmp_filename = self.helper.make_wav(os.path.join(self._in_fixtures, 'lamb_stereo.wav'))

        # Compare the created file to one we made earlier
        self.assertTrue(filecmp.cmp(self.tmp_filename, self.expected_output_file('lamb_from_stereo.wav')))

    def test_mp3_file_creation_from_stereo_wav(self):
        self.tmp_filename = self.helper.make_mp3(os.path.join(self._in_fixtures, 'lamb_stereo.wav'))

        # Compare the created file to one we made earlier
        self.assertTrue(filecmp.cmp(self.tmp_filename, self.expected_output_file('lamb_mp3_from_stereo.mp3')))

    def test_mp3_file_creation_from_iphone_wav(self):
        self.tmp_filename = self.helper.make_mp3(os.path.join(self._in_fixtures, 'lamb_iphone.wav'))

        # Compare the created file to one we made earlier
        self.assertTrue(filecmp.cmp(self.tmp_filename, self.expected_output_file('lamb_mp3_from_iphone.mp3')))

    def test_mp3_file_creation_from_android_3gp(self):
        self.tmp_filename = self.helper.make_mp3(os.path.join(self._in_fixtures, 'lamb.3gp'))

        # Compare the created file to one we made earlier
        self.assertTrue(filecmp.cmp(self.tmp_filename, self.expected_output_file('lamb_mp3_from_3gp.mp3')))

    def test_recording_splitting_no_timestamps(self):
        audio = open(os.path.join(self._in_fixtures, 'lamb.mp3'), 'rb')
        recording = Recording.objects.create(audio=File(audio, 'lamb.mp3'))

        files_created = self.helper.split_recording(recording)

        self.assertEquals(len(files_created), 1)
        self.assertTrue(filecmp.cmp(files_created[0], self.expected_output_file('lamb_whole.mp3')))

    def test_recording_splitting_one_timestamp(self):
        speaker = Speaker.objects.create(popit_url='http://popit.mysociety.org/api/v1/person/abcd', name='Steve')
        timestamp = RecordingTimestamp.objects.create(speaker=speaker, timestamp=timezone.now())
        audio = open(os.path.join(self._in_fixtures, 'lamb.mp3'), 'rb')
        recording = Recording.objects.create(audio=File(audio, 'lamb.mp3'))
        recording.timestamps.add(timestamp)
        recording.save()

        files_created = self.helper.split_recording(recording)

        self.assertEquals(len(files_created), 1)
        self.assertTrue(filecmp.cmp(files_created[0], self.expected_output_file('lamb_whole.mp3')))

    def test_recording_splitting_several_timestamps(self):
        speaker1 = Speaker.objects.create(popit_url='http://popit.mysociety.org/api/v1/person/abcd', name='Steve')
        speaker2 = Speaker.objects.create(popit_url='http://popit.mysociety.org/api/v1/person/efgh', name='Dave')
        speaker3 = Speaker.objects.create(popit_url='http://popit.mysociety.org/api/v1/person/ijkl', name='Struan')
        start = timezone.now()
        timestamp1 = RecordingTimestamp.objects.create(speaker=speaker1, timestamp=start)
        start_plus_3_seconds = start + timedelta(seconds=3)
        timestamp2 = RecordingTimestamp.objects.create(speaker=speaker2, timestamp=start_plus_3_seconds)
        start_plus_4_seconds = start + timedelta(seconds=4)
        timestamp3 = RecordingTimestamp.objects.create(speaker=speaker3, timestamp=start_plus_4_seconds)
        audio = open(os.path.join(self._in_fixtures, 'lamb.mp3'), 'rb')
        recording = Recording.objects.create(audio=File(audio, 'lamb.mp3'))
        recording.timestamps.add(timestamp1)
        recording.timestamps.add(timestamp2)
        recording.timestamps.add(timestamp3)
        recording.save()

        files_created = self.helper.split_recording(recording)

        self.assertEquals(len(files_created), 3)
        self.assertTrue(filecmp.cmp(files_created[0], self.expected_output_file('lamb_first_three_seconds.mp3')))
        self.assertTrue(filecmp.cmp(files_created[1], self.expected_output_file('lamb_from_three_to_four_seconds.mp3')))
        self.assertTrue(filecmp.cmp(files_created[2], self.expected_output_file('lamb_from_four_seconds_onwards.mp3')))
