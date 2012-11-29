import subprocess
import tempfile
import os
import requests
from celery import task
from django.conf import settings
from speeches.models import Speech

@task()
def transcribe_speech(speech_id):
    """Celery task to transcribe the audio for the given speech"""

    # Note we don't try to catch exceptions which might cause a failure here
    # because celery will see them and report a failure back to whatever called
    # this task, and it's their problem then!

    # Check speech is ok to be transcribed
    speech = Speech.objects.get(id=speech_id)
    helper = TranscribeHelper();
    helper.check_speech(speech)

    # Make an 8khz version of the audio using mpg123
    # First make a temporary file
    (fd, tmp_filename) = tempfile.mkstemp(suffix='.wav')
    try:
        if helper.make_wav(tmp_filename, speech.audio.path):
            # mpg123 completed successfully, so upload it to AT&T
            # First we need an oauth token
            auth_token = helper.get_oauth_token()
            # Now we can use that token to make a request
            transcription = helper.get_transcription(auth_token, tmp_filename)
            # Then we're done - save in db and return transcription to caller
            speech.text = transcription
            # Wipe the celery task id too
            speech.celery_task_id = None
            speech.save()
            return transcription
        else:
            # Something went wrong with mpg123
            raise TranscribeException(
                'MPG to WAV conversion did not complete successfully')
    finally:
        os.remove(tmp_filename)

class TranscribeException(Exception):
    """Custom exception class for errors that occur with transcribing that 
       aren't covered by existing exeptions"""
    pass

class TranscribeHelper():
    def check_speech(self, speech):
        """Check that the supplied speech is ok to transcribe, ie: it has audio
           and no text"""
        if speech.audio is None:
                raise TranscribeException(
                    'Speech: {0} has no audio file!'.format(speech.id))
        if speech.text.strip():
                raise TranscribeException(
                    'Speech: {0} is already transcribed!'.format(speech.id))   

    def make_wav(self, tmp_filename, speech_filename):
        """Make a .wav file suitable for uploading to AT&T and return true if
        it succeeded"""
        result = subprocess.call([
            'mpg123',
            '-q',
            '--mono', 
            '--rate',
            '8000', 
            '-w',
            tmp_filename, 
            speech_filename
        ])
        return result == 0

    def get_oauth_token(self):
        """Get an oauth token from AT&T for the Speech service"""
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
        token_r = requests.post(settings.ATT_OAUTH_URL,
                                headers=token_headers,
                                data=token_payload)
        
        # Check the response was ok
        if(token_r.status_code != requests.codes.ok):
            token_r.raise_for_status();

        return token_r.json['access_token']

    def get_transcription(self, auth_token, filename):
        """Get a transcription from AT&T for the given file"""  
        request_headers = {
            'Authorization': 'Bearer ' + auth_token,
            'Content-type': 'audio/wav',
            'Accept': 'application/json',
            'X-SpeechContext': 'Generic'
        }
        transcribe_r = requests.post(settings.ATT_API_URL,
                                     headers=request_headers,
                                     data=open(filename, 'rb'))

        # Check response was ok
        if(transcribe_r.status_code != requests.codes.ok):
            transcribe_r.raise_for_status()

        # Get the response json as a python object
        transcription_response = transcribe_r.json

        # Get the best transcription from the response
        transcription = self.best_transcription(transcription_response)
        if(transcription is None):
            raise TranscribeException(
                "AT&T could not transcribe the audio, they returned:\n" +
                 transcribe_r.text)

        return transcription       

    def best_transcription(self, response):
        """Return the transcription with the highest confidence or None if 
           there are no good transcriptions"""

        # Get the actual results from the response object
        transcriptions = response['Recognition']['NBest']
        
        if(len(transcriptions) == 0):
            return None
        
        # Sort the results by their Confidence
        transcriptions.sort(key = lambda x: x['Confidence'])

        # Return the result with the highest confidence, unless
        # even that one is poor.
        # TODO - maybe relying on AT&T's grading isn't best here,
        # we could look at the Confidence level ourselves.
        if(transcriptions[0]['Grade'] != "Reject"):
            return transcriptions[0]['ResultText']

        # Nothing else is good enough
        return None