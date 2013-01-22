import os
import tempfile
import filecmp

from django.test import TestCase
from django.core.files import File

import speeches
from speeches.utils import AudioHelper

class AudioHelperTests(TestCase):

    @classmethod
    def setUpClass(cls):
        cls._speeches_path = os.path.abspath(speeches.__path__[0])

    def test_wav_file_creation_from_mp3(self):
        helper = AudioHelper()

        (fd, tmp_filename) = tempfile.mkstemp(suffix='.wav')
        helper.make_wav(os.path.join(self._speeches_path, 'fixtures', 'lamb.mp3'), tmp_filename)

        # Compare the created file to one we made earlier
        self.assertTrue(filecmp.cmp(tmp_filename, os.path.join(self._speeches_path, 'fixtures', 'lamb_from_mp3.wav')))

    def test_wav_file_creation_from_android_3gp(self):
        helper = AudioHelper()

        (fd, tmp_filename) = tempfile.mkstemp(suffix='.wav')
        helper.make_wav(os.path.join(self._speeches_path, 'fixtures', 'lamb.3gp'), tmp_filename)

        # Compare the created file to one we made earlier
        self.assertTrue(filecmp.cmp(tmp_filename, os.path.join(self._speeches_path, 'fixtures', 'lamb_from_3gp.wav')))

    def test_wav_file_creation_from_iphone_wav(self):
        helper = AudioHelper()

        (fd, tmp_filename) = tempfile.mkstemp(suffix='.wav')
        helper.make_wav(os.path.join(self._speeches_path, 'fixtures', 'lamb_iphone.wav'), tmp_filename)

        # Compare the created file to one we made earlier
        self.assertTrue(filecmp.cmp(tmp_filename, os.path.join(self._speeches_path, 'fixtures', 'lamb_from_iphone.wav')))

    def test_wav_file_creation_from_stereo_wav(self):
        helper = AudioHelper()

        (fd, tmp_filename) = tempfile.mkstemp(suffix='.wav')
        helper.make_wav(os.path.join(self._speeches_path, 'fixtures', 'lamb_stereo.wav'), tmp_filename)

        # Compare the created file to one we made earlier
        self.assertTrue(filecmp.cmp(tmp_filename, os.path.join(self._speeches_path, 'fixtures', 'lamb_from_stereo.wav')))
