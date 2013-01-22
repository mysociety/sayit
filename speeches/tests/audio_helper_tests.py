import os
import tempfile
import filecmp

from django.test import TestCase
from django.core.files import File

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

        self.helper.split_recording(recording, tmp_folder)

        count_files_created = len([name for name in os.listdir(tmp_folder) if os.path.isfile(name)])

        self.assertEquals(count_files_created, 0)