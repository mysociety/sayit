from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import subprocess
import tempfile
import os
from speeches.models import Speech

class Command(BaseCommand):
    args = '<speech_id, speech_id ...>'
    help = 'Transcribes speeches with AT&T\'s external webservice'

    def handle(self, *args, **options):
        # Do some transcribing

        # Check we've been given at least one speech id to transcribe
        if (len(args) == 0):
            raise CommandError('No poll ids supplied')

        # Transcribe each file we've been given
        for speech_id in args:
            self.stdout.write("Processing speech id: " + speech_id + "\n")

            # Check speech is ok to be transcribed
            try:
                speech = Speech.objects.get(id=speech_id)
            except Speech.DoesNotExist:
                raise CommandError('Speech: {0} does not exist'.format(speech_id))

            if speech.audio is None:
                raise CommandError('Speech: {0} has no audio file!'.format(speech_id))

            if speech.text.strip():
                raise CommandError('Speech: {0} already has a transcription!'.format(speech_id))                

            # Make an 8khz version of the audio using mpg123
            # First make a temporary file
            (fd, tmp_filename) = tempfile.mkstemp(suffix='.wav')
            try:
                result = subprocess.call([
                    'mpg123',
                    '-q',
                    '--mono', 
                    '--rate',
                    '8000', 
                    '-w',
                    tmp_filename, 
                    speech.audio.path
                ])
                if result == 0:
                    # mpg123 completed successfully
                    self.stdout.write('File for uploading is at ' + tmp_filename)
                    
                    # Upload it to AT&T

                    # Save the transcription in the db

                else:
                    # Something went wrong with mpg123
                    raise CommandError('MPG to WAV conversion did not complete successfully')

            except (subprocess.CalledProcessError, OSError) as e:
                # Something went wrong before mpg123 was running
                raise CommandError('Error running mpg123:\n' + e.strerror)
            finally:
                # Remove the temp file
                os.remove(tmp_filename)
