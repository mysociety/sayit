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
        cls._speeches_path = os.path.abspath(speeches.__path__[0])

    def setUp(self):
        self.helper = AudioHelper()

    def test_wav_file_creation_from_mp3(self):
        (fd, tmp_filename) = tempfile.mkstemp(suffix='.wav')
        self.helper.make_wav(os.path.join(self._speeches_path, 'fixtures', 'lamb.mp3'), tmp_filename)

        # Compare the created file to one we made earlier
        self.assertTrue(filecmp.cmp(tmp_filename, os.path.join(self._speeches_path, 'fixtures', 'lamb_from_mp3.wav')))

    def test_wav_file_creation_from_android_3gp(self):
        (fd, tmp_filename) = tempfile.mkstemp(suffix='.wav')
        self.helper.make_wav(os.path.join(self._speeches_path, 'fixtures', 'lamb.3gp'), tmp_filename)

        # Compare the created file to one we made earlier
        self.assertTrue(filecmp.cmp(tmp_filename, os.path.join(self._speeches_path, 'fixtures', 'lamb_from_3gp.wav')))

    def test_wav_file_creation_from_iphone_wav(self):
        (fd, tmp_filename) = tempfile.mkstemp(suffix='.wav')
        self.helper.make_wav(os.path.join(self._speeches_path, 'fixtures', 'lamb_iphone.wav'), tmp_filename)

        # Compare the created file to one we made earlier
        self.assertTrue(filecmp.cmp(tmp_filename, os.path.join(self._speeches_path, 'fixtures', 'lamb_from_iphone.wav')))

    def test_wav_file_creation_from_stereo_wav(self):
        (fd, tmp_filename) = tempfile.mkstemp(suffix='.wav')
        self.helper.make_wav(os.path.join(self._speeches_path, 'fixtures', 'lamb_stereo.wav'), tmp_filename)

        # Compare the created file to one we made earlier
        self.assertTrue(filecmp.cmp(tmp_filename, os.path.join(self._speeches_path, 'fixtures', 'lamb_from_stereo.wav')))

    def test_mp3_file_creation_from_stereo_wav(self):
        (fd, tmp_filename) = tempfile.mkstemp(suffix='.mp3')
        self.helper.make_mp3(os.path.join(self._speeches_path, 'fixtures', 'lamb_stereo.wav'), tmp_filename)

        # Compare the created file to one we made earlier
        self.assertTrue(filecmp.cmp(tmp_filename, os.path.join(self._speeches_path, 'fixtures', 'lamb_mp3_from_stereo.mp3')))

    def test_mp3_file_creation_from_iphone_wav(self):
        (fd, tmp_filename) = tempfile.mkstemp(suffix='.mp3')
        self.helper.make_mp3(os.path.join(self._speeches_path, 'fixtures', 'lamb_iphone.wav'), tmp_filename)

        # Compare the created file to one we made earlier
        self.assertTrue(filecmp.cmp(tmp_filename, os.path.join(self._speeches_path, 'fixtures', 'lamb_mp3_from_iphone.mp3')))

    def test_mp3_file_creation_from_android_3gp(self):
        (fd, tmp_filename) = tempfile.mkstemp(suffix='.mp3')
        self.helper.make_mp3(os.path.join(self._speeches_path, 'fixtures', 'lamb.3gp'), tmp_filename)

        # Compare the created file to one we made earlier
        self.assertTrue(filecmp.cmp(tmp_filename, os.path.join(self._speeches_path, 'fixtures', 'lamb_mp3_from_3gp.mp3')))

    def test_recording_splitting_no_timestamps(self):
        audio = open(os.path.join(self._speeches_path, 'fixtures', 'lamb.mp3'), 'rb')
        recording = Recording.objects.create(audio=File(audio, 'lamb.mp3'))

        tmp_folder = tempfile.mkdtemp()

        print("tmp_folder: {0}".format(tmp_folder))

        result = self.helper.split_recording(recording, tmp_folder)

        count_files_created = len([name for name in os.listdir(tmp_folder)])

        self.assertTrue(result)
        self.assertEquals(count_files_created, 1)

    def test_recording_splitting_one_timestamp(self):
        speaker = Speaker.objects.create(popit_url='http://popit.mysociety.org/api/v1/person/abcd', name='Steve')
        timestamp = RecordingTimestamp.objects.create(speaker=speaker, timestamp=timezone.now())
        audio = open(os.path.join(self._speeches_path, 'fixtures', 'lamb.mp3'), 'rb')
        recording = Recording.objects.create(audio=File(audio, 'lamb.mp3'))
        recording.timestamps.add(timestamp)
        recording.save()

        tmp_folder = tempfile.mkdtemp()

        result = self.helper.split_recording(recording, tmp_folder)

        count_files_created = len([name for name in os.listdir(tmp_folder)])

        self.assertTrue(result)
        self.assertEquals(count_files_created, 1)

    def test_recording_splitting_several_timestamps(self):
        speaker1 = Speaker.objects.create(popit_url='http://popit.mysociety.org/api/v1/person/abcd', name='Steve')
        speaker2 = Speaker.objects.create(popit_url='http://popit.mysociety.org/api/v1/person/efgh', name='Dave')
        now = timezone.now()
        timestamp1 = RecordingTimestamp.objects.create(speaker=speaker1, timestamp=now)
        now_plus_3_seconds = now + timedelta(seconds=3)
        timestamp2 = RecordingTimestamp.objects.create(speaker=speaker2, timestamp=now_plus_3_seconds)
        audio = open(os.path.join(self._speeches_path, 'fixtures', 'lamb.mp3'), 'rb')
        recording = Recording.objects.create(audio=File(audio, 'lamb.mp3'))
        recording.timestamps.add(timestamp1)
        recording.timestamps.add(timestamp2)
        recording.save()

        tmp_folder = tempfile.mkdtemp()

        result = self.helper.split_recording(recording, tmp_folder)

        count_files_created = len([name for name in os.listdir(tmp_folder)])

        self.assertTrue(result)
        self.assertEquals(count_files_created, 2)