import os
import subprocess
import mimetypes
import logging
import tempfile
import calendar
from itertools import groupby
from operator import itemgetter
from datetime import datetime

import requests
import pytz

from django.conf import settings
from django.forms.models import ModelChoiceIterator, ModelChoiceField

logger = logging.getLogger(__name__)

"""Common utility functions/classes
Things that are needed by multiple bits of code but are specific enough to
this project not to be in a separate python package"""

# From http://djangosnippets.org/snippets/2622/
class GroupedModelChoiceField(ModelChoiceField):
    def __init__(self, queryset, group_by_field, group_label=None, *args, **kwargs):
        """
        group_by_field is the name of a field on the model
        group_label is a function to return a label for each choice group
        """
        super(GroupedModelChoiceField, self).__init__(queryset, *args, **kwargs)
        self.group_by_field = group_by_field
        if group_label is None:
            self.group_label = lambda group: group
        else:
            self.group_label = group_label

    def _get_choices(self):
        """
        Exactly as per ModelChoiceField except returns new iterator class
        """
        if hasattr(self, '_choices'):
            return self._choices
        return GroupedModelChoiceIterator(self)
    choices = property(_get_choices, ModelChoiceField._set_choices)

# From http://djangosnippets.org/snippets/2622/
class GroupedModelChoiceIterator(ModelChoiceIterator):
    def __iter__(self):
        if self.field.empty_label is not None:
            yield (u"", self.field.empty_label)
        if self.field.cache_choices:
            if self.field.choice_cache is None:
                self.field.choice_cache = [
                    (self.field.group_label(group), [self.choice(ch) for ch in choices])
                        for group,choices in groupby(self.queryset.all(),
                            key=lambda row: getattr(row, self.field.group_by_field))
                ]
            for choice in self.field.choice_cache:
                yield choice
        else:
            for group, choices in groupby(self.queryset.all(),
                    key=lambda row: getattr(row, self.field.group_by_field)):
                yield (self.field.group_label(group), [self.choice(ch) for ch in choices])

class TranscribeException(Exception):
    """Custom exception class for errors that occur with transcribing that
       aren't covered by existing exeptions"""
    pass

class TranscribeHelper(object):
    """Helper class to contain functions for transcribing audio"""

    def check_speech(self, speech):
        """Check that the supplied speech is ok to transcribe, ie: it has audio
           and no text"""
        if not bool(speech.audio):
            raise TranscribeException(
                    'Speech: {0} has no audio file!'.format(speech.id))
        if speech.text.strip():
            raise TranscribeException(
                    'Speech: {0} is already transcribed!'.format(speech.id))

    def get_oauth_token(self):
        """Get an oauth token from AT&T for the Speech service"""

        logger.info("Getting auth token")

        # TODO - I think there might be a nicer way to do this with the
        # built-in oauth stuff that the requests module offers
        token_headers = {
            'Accept': 'application/x-www-form-urlencoded',
            'Content-type': 'application/x-www-form-urlencoded',
        }
        token_payload = {
            'client_id': settings.ATT_CLIENT_ID,
            'client_secret': settings.ATT_SECRET,
            'grant_type': 'client_credentials',
            'scope': 'SPEECH'
        }

        try:
            token_r = requests.post(settings.ATT_OAUTH_URL,
                                    headers=token_headers,
                                    data=token_payload,
                                    timeout=settings.ATT_TIMEOUT)

            # Check the response was ok
            if(token_r.status_code != requests.codes.ok):
                logger.error("Auth request returned: {0}\n{1}".format(token_r.status_code, token_r.text))
                token_r.raise_for_status()
        except requests.exceptions.RequestException as e:
            logger.error("Transcription Auth API returned an error: {0}".format(e))
            raise TranscribeException("Transcription Auth API returned an error: {0}".format(e))

        return token_r.json['access_token']

    def get_transcription(self, filename):
        """Get a transcription from AT&T for the given file"""

        logger.info("Getting transcription for filename: " + filename)

        # First we need an oauth token
        auth_token = self.get_oauth_token()

        # Guess the mimetype from the file
        (mime_type, encoding) = mimetypes.guess_type(filename, strict=False)
        logger.info("Mime type guessed as: {0}".format(mime_type))
        if mime_type is None:
            # Choose a default instead
            logger.info("Setting mime type to default (audio/wav)")
            mime_type = "audio/wav"

        request_headers = {
            'Authorization': 'Bearer ' + auth_token,
            'Content-type': mime_type,
            'Accept': 'application/json',
            'X-SpeechContext': 'Generic'
        }

        try:
            transcribe_r = requests.post(settings.ATT_API_URL,
                                         headers=request_headers,
                                         data=open(filename, 'rb'),
                                         timeout=settings.ATT_TIMEOUT)

            # Check response was ok
            if(transcribe_r.status_code != requests.codes.ok):
                logger.error("API request returned: {0}\n{1}"
                        .format(transcribe_r.status_code, transcribe_r.text))
                transcribe_r.raise_for_status()
        except requests.exceptions.RequestException as e:
            logger.error("Transcription API returned an error: {0}".format(e));
            raise TranscribeException("Transcription API returned an error: {0}".format(e))

        # Get the response json as a python object
        transcription_response = transcribe_r.json

        # Get the best transcription from the response
        transcription = self.best_transcription(transcription_response)
        if(transcription is None):
            logger.error("AT&T could not transcribe the audio, they returned:\n{0}"
                .format(transcribe_r.text))
            raise TranscribeException(
                "AT&T could not transcribe the audio, they returned:\n{0}"
                    .format(transcribe_r.text))

        return transcription

    def best_transcription(self, response):
        """Return the transcription with the highest confidence or None if
           there are no good transcriptions"""

        # Get the actual results from the response object
        transcriptions = response['Recognition']['NBest']

        if(len(transcriptions) == 0):
            return None

        # Sort the results by their Confidence
        sorted_transcriptions = sorted(transcriptions, key=itemgetter('Confidence'), reverse=True)

        # Return the result with the highest confidence, unless
        # even that one is poor.
        # TODO - maybe relying on AT&T's grading isn't best here,
        # we could look at the Confidence level ourselves.
        if(sorted_transcriptions[0]['Grade'] != "reject"):
            return sorted_transcriptions[0]['ResultText']

        # Nothing else is good enough
        return None

class AudioException(Exception):
    """Custom exception for audio transcoding ThingsThatGoWrong"""
    pass

class AudioHelper(object):

    def make_wav(self, in_filename):
        """Make a .wav file suitable for uploading to AT&T and return true if
           it succeeded"""
        # First make a temporary file
        (fd, out_filename) = tempfile.mkstemp(suffix='.wav')

        options = self._build_ffmpeg_options(in_filename)
        options.extend([
            # Output options
            # Sample rate of 8KHz
            '-ar',
            '8000',
            # Single channel, ie: mono
            '-ac',
            '1',
            # Use the 16-bit pcm codec
            '-acodec',
            'pcm_s16le',
            # Output file
            out_filename

        ])

        with open(os.devnull, 'w') as dev_null:
            result = subprocess.call(options, stderr=dev_null)

        if not result == 0:
            message = "FFMPEG failed to make .wav with result: {0} on file: {1}".format(result, in_filename)
            logger.error(message)
            raise AudioException(message)

        return out_filename

    def make_mp3(self, in_filename):
        """Make a .mp3 file suitable for displaying publically on the website, returns
           the filename if it succeeded, and throws an AudioException if something went wrong"""
        (fd, out_filename) = tempfile.mkstemp(suffix=".mp3")
        options = self._build_ffmpeg_options(in_filename)
        options.extend(self._build_ffmpeg_mp3_output_options(out_filename))
        with open(os.devnull, 'w') as dev_null:
            result = subprocess.call(options, stderr=dev_null)
        if not result == 0:
            message = "FFMPEG failed to make .mp3 with result: {0} on file: {1}".format(result, in_filename)
            logger.error(message)
            raise AudioException(message)

        return out_filename

    def split_recording(self, recording):
        """Make a series of .mp3 files from one recording, based on its timestamps"""

        # List of files we'll return
        files = []

        # Does it have any audio?
        if not recording.audio:
            logger.error("Asked to split recording: {0} with no audio, returning immediately".format(recording))
            return files

        # Do we have any timestamps to split it by?
        if not recording.timestamps or recording.timestamps.count() <= 1:
            # None, or one - just make an mp3 of the whole thing
            logger.info("No timestamps in the recording: {0} or only one, so making an mp3 of all of it.".format(recording))
            files.append(self.make_mp3(recording.audio.path))
            return files

        # We have more than one timestamp
        sorted_timestamps = recording.timestamps.all().order_by("timestamp")
        start_timestamp = sorted_timestamps[0]
        for index, timestamp in enumerate(sorted_timestamps):
            next_timestamp = None
            if index < (len(sorted_timestamps) - 1):
                next_timestamp = sorted_timestamps[index + 1]

            files.append(self.make_partial_mp3(recording, start_timestamp, timestamp, next_timestamp))

        return files

    def make_partial_mp3(self, recording, start_timestamp, timestamp, next_timestamp):
        """Make a partial mp3 file for a given timestamp"""
        # We assume the first timestamp is 00:00:00 in the recording
        # so we can then calculate the other offsets from there.

        # Work out the time this timestamp starts, in seconds from the start of the recording
        start_time_relative = timestamp.utc - start_timestamp.utc

        # Work out the time this timestamp ends, in seconds from the start
        end_time_relative = None
        if next_timestamp is not None:
            end_time_relative = next_timestamp.utc - start_timestamp.utc

        (fd, out_filename) = tempfile.mkstemp(suffix=".mp3")

        options = self._build_ffmpeg_options(recording.audio.path)
        # Where to start from
        options.extend(["-ss", str(start_time_relative)])
        # Where to go to
        if end_time_relative is not None:
            options.extend(['-t', str(end_time_relative)])
        options.extend(self._build_ffmpeg_mp3_output_options(out_filename))

        with open(os.devnull, 'w') as dev_null:
            result = subprocess.call(options, stderr=dev_null)

        # Check that the result was ok, and if not, blow up
        if not result == 0:
            message = "FFMPEG failed with result: {0} on timestamp: {1}".format(result, timestamp)
            logger.error(message)
            raise AudioException(message)

        return out_filename


    def _build_ffmpeg_options(self, in_filename):
        return [
            'ffmpeg',
            # Tell ffmpeg to shut up
            '-loglevel',
            '0',
            # Say yes to everything
            '-y',
            # Input file
            '-i',
            in_filename
        ]

    def _build_ffmpeg_mp3_output_options(self, out_filename):
        return [
            # Output options
            # 128 kbps bitrate
            '-ab',
            '128k',
            '-acodec',
            'libmp3lame',
            # Output file
            out_filename
        ]



