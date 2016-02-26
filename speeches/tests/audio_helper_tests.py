import audioread.ffdec
import mutagen
import os
import re
import wave
from datetime import timedelta

from django.core.files import File
from django.utils import timezone

import speeches
from speeches.tests import InstanceTestCase
from speeches.utils.audio import AudioHelper
from speeches.models import Recording, RecordingTimestamp, Speaker


def strip_kbps_from_file_info(s):
    return re.sub(r'\s+\d+\s+kbps,', '', s)


def file_info(filename):
    if filename.endswith('.mp3'):
        mp3 = mutagen.File(filename)
        return (mp3.tags.version, mp3.info.layer, mp3.info.version, mp3.info.sample_rate, mp3.info.mode)
    elif filename.endswith('.wav'):
        wav = wave.open(filename)
        return (wav.getsampwidth(), wav.getnchannels(), wav.getframerate())


class AudioHelperTests(InstanceTestCase):

    @classmethod
    def setUpClass(cls):
        cls._in_fixtures = os.path.join(os.path.abspath(speeches.__path__[0]), 'fixtures', 'test_inputs')
        cls._expected_fixtures = os.path.join(os.path.abspath(speeches.__path__[0]), 'fixtures', 'expected_outputs')
        super(AudioHelperTests, cls).setUpClass()

    def setUp(self):
        super(AudioHelperTests, self).setUp()
        self.helper = AudioHelper()
        self.tmp_filename = None
        self.remove_tmp_filename = False

    def tearDown(self):
        if self.tmp_filename is not None and self.remove_tmp_filename:
            os.remove(self.tmp_filename)

    def expected_output_file(self, filename):
        _, extension = os.path.splitext(filename)
        return os.path.join(self._expected_fixtures,
                            extension[1:],
                            filename)

    def assertSameAudioLength(self, filename_a, filename_b):
        files = (filename_a, filename_b)
        # Use FFMPEG directly as CoreAudio returns incorrect durations for the generated MP3s
        af1 = audioread.ffdec.FFmpegAudioFile(filename_a)
        af2 = audioread.ffdec.FFmpegAudioFile(filename_b)
        message = 'The audio files %s (%.3fs) and %s (%.3fs) were of different lengths'
        message = message % (files[0], af1.duration, files[1], af2.duration)
        # Make sure the lengths are within 0.2s of each other - this is
        # intended to be imprecise enough to ignore any differences in
        # frame padding in the MP3:
        self.assertAlmostEqual(af1.duration,
                               af2.duration,
                               delta=0.2,
                               msg=message)

    def convert(self, known_input, method, expected_output):
        self.tmp_filename = getattr(self.helper, method)(os.path.join(self._in_fixtures, known_input))
        expected = self.expected_output_file(expected_output)
        # Check that the type of the file is exactly the same first of all:
        self.assertEqual(file_info(self.tmp_filename), file_info(expected))
        # Now check that the files are identical:
        self.assertSameAudioLength(self.tmp_filename, expected)

    def test_wav_file_creation_from_mp3(self):
        self.convert('lamb.mp3', 'make_wav', 'lamb_from_mp3.wav')

    def test_wav_file_creation_from_android_3gp(self):
        self.convert('lamb.3gp', 'make_wav', 'lamb_from_3gp.wav')

    def test_wav_file_creation_from_iphone_wav(self):
        self.convert('lamb_iphone.wav', 'make_wav', 'lamb_from_iphone.wav')

    def test_wav_file_creation_from_stereo_wav(self):
        self.convert('lamb_stereo.wav', 'make_wav', 'lamb_from_stereo.wav')

    def test_mp3_file_creation_from_stereo_wav(self):
        self.convert('lamb_stereo.wav', 'make_mp3', 'lamb_mp3_from_stereo.mp3')

    def test_mp3_file_creation_from_iphone_wav(self):
        self.convert('lamb_iphone.wav', 'make_mp3', 'lamb_mp3_from_iphone.mp3')

    def test_mp3_file_creation_from_android_3gp(self):
        self.convert('lamb.3gp', 'make_mp3', 'lamb_mp3_from_3gp.mp3')

    def test_recording_splitting_no_timestamps(self):
        audio = open(os.path.join(self._in_fixtures, 'lamb.mp3'), 'rb')
        recording = Recording.objects.create(audio=File(audio, 'lamb.mp3'), instance=self.instance)

        files_created = self.helper.split_recording(recording)

        self.assertEqual(len(files_created), 1)
        self.assertSameAudioLength(files_created[0], self.expected_output_file('lamb_whole.mp3'))

    def test_recording_splitting_one_timestamp(self):
        speaker = Speaker.objects.create(name='Steve', instance=self.instance)
        timestamp = RecordingTimestamp.objects.create(
            speaker=speaker, timestamp=timezone.now(), instance=self.instance)
        audio = open(os.path.join(self._in_fixtures, 'lamb.mp3'), 'rb')
        recording = Recording.objects.create(
            audio=File(audio, 'lamb.mp3'), instance=self.instance, start_datetime=timestamp.timestamp)
        recording.timestamps.add(timestamp)
        recording.save()

        files_created = self.helper.split_recording(recording)

        self.assertEqual(len(files_created), 1)
        self.assertSameAudioLength(files_created[0], self.expected_output_file('lamb_whole.mp3'))

    def test_recording_splitting_several_timestamps(self):
        speakers = []
        for i in range(3):
            speakers.append(Speaker.objects.create(name='Steve %d' % i, instance=self.instance))

        start = timezone.now()
        timestamps = [0, 3, 4]
        for i in range(3):
            start_i = start + timedelta(seconds=timestamps[i])
            timestamps[i] = RecordingTimestamp.objects.create(
                speaker=speakers[i], timestamp=start_i, instance=self.instance)

        audio = open(os.path.join(self._in_fixtures, 'lamb.mp3'), 'rb')
        recording = Recording.objects.create(
            audio=File(audio, 'lamb.mp3'), instance=self.instance, start_datetime=timestamps[0].timestamp)
        for i in range(3):
            recording.timestamps.add(timestamps[i])
        recording.save()

        files_created = self.helper.split_recording(recording)

        self.assertEqual(len(files_created), 3)
        files = [
            'lamb_first_three_seconds.mp3',
            'lamb_from_three_to_four_seconds.mp3',
            'lamb_from_four_seconds_onwards.mp3',
        ]
        for i in range(3):
            self.assertSameAudioLength(files_created[i], self.expected_output_file(files[i]))

    def test_audio_length(self):
        audio_path = os.path.join(self._in_fixtures, 'lamb.mp3')
        duration = self.helper.get_audio_duration(audio_path)
        self.assertEqual(duration, 5)
