from speeches.tasks import transcribe_speech
from django.forms.widgets import SplitDateTimeWidget

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

class BootstrapSplitDateTimeWidget(SplitDateTimeWidget):
    """
    A Widget that splits datetime input into two <input type="text"> boxes and styles with Bootstrap
    """

    def __init__(self, attrs=None, date_format=None, time_format=None):
        super(BootstrapSplitDateTimeWidget, self).__init__(attrs, date_format, time_format)

    def format_output(self, rendered_widgets):
        """Override the output formatting to return widgets with some Bootstrap niceness"""
        
        output = ''
        
        for i, widget in enumerate(rendered_widgets):
            output += '<div class="input-append">'
            output += widget
            if i == 0:
                output += '<span class="add-on"><i class="icon-calendar"></i></span>'
            else:
                output += '<span class="add-on"><i class="icon-time"></i></span>'
            output += '</div>'

        return output