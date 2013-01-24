import tempfile
import os

from celery import task
from celery.utils.log import get_task_logger

from django.conf import settings

from speeches.models import Speech
from speeches.utils import TranscribeHelper, TranscribeException, AudioHelper, AudioException

logger = get_task_logger(__name__)

@task()
def transcribe_speech(speech_id):
    """Celery task to transcribe the audio for the given speech"""

    # Note, we have to catch exceptions to be able to retry them if we want
    # to, at the moment we just give up
    speech = Speech.objects.get(id=speech_id)
    default_transcription = settings.DEFAULT_TRANSCRIPTION
    try:
        # Check speech is ok to be transcribed
        transcribe_helper = TranscribeHelper();
        transcribe_helper.check_speech(speech)

        # Convert to wav
        audio_helper = AudioHelper();
        # Make an 8khz version of the audio using ffmpeg
        tmp_filename = None
        try:
            tmp_filename = audio_helper.make_wav(speech.audio.path)
            transcription = transcribe_helper.get_transcription(tmp_filename)
            # Save the result into the DB
            speech.text = transcription
        finally:
            if tmp_filename is not None:
                os.remove(tmp_filename)

        return transcription

    except (AudioException, TranscribeException, OSError) as e:
        # We could retry here with something like:

        # backoff = 2 ** transcribe_speech.request.retries
        # transcribe_speech.retry(exc=e, countdown=backoff)

        # But for now we just give up
        if not speech.text:
            speech.text = default_transcription
    finally:
        # Wipe the celery task id and save the speech no matter what happens
        # TODO - would this work in the case of a retry?
        speech.celery_task_id = None
        speech.save()
