from speeches.tasks import transcribe_speech

"""Common utility functions/classes
Things that are needed by multiple bits of code but are specific enough to
this project not to be in a separate python package"""

def start_transcribing_speech(speech):
    """Kick off a celery task to transcribe a speech"""
    # We only do anything if there's no text already
    if not speech.text:
        # If someone is adding a new audio file and there's already a task
        # We need to clear it
        if speech.celery_task_id:   
            celery.task.control.revoke(speech.celery_task_id)
        # Now we can start a new one
        result = transcribe_speech.delay(speech.id)
        # Finally, we can remember the new task in the model
        speech.celery_task_id = result.task_id
        speech.save()