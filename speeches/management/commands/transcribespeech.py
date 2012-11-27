from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from subprocess import call, CalledProcessError
from speeches.models import Speech

class Command(BaseCommand):
    args = '<speech_id, speech_id ...>'
    help = 'Transcribes speeches with AT&T\'s external webservice'

    def handle(self, *args, **options):
        # Do some transcribing
        if (len(args) == 0):
            raise CommandError('No poll ids supplied')

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

            # Get speech audio file
            # audio_file = speech.audio.open(mode='r')          

            # Make an 8khz version using mpg123
            try:
                result = call(['mpg123', '--mono --rate 8000 -w /tmp/test-output-file.wav {0}'.format(speech.audio.path)])
                if result == 0:
                    # Upload it to AT&T
                    # Save the transcription in the db
                    self.stdout.write('File for uploading is at /tmp/test-output-file.wav')
            except (CalledProcessError, OSError) as e:
                raise CommandError('Error converting file {0} to 8khz WAV for AT&T:\n{1}'.format(speech.audio.path, e.strerror))
