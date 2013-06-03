import os
import logging
from datetime import datetime
import pytz

from django_select2.widgets import Select2Widget, Select2MultipleWidget

from django import forms
from django.forms.forms import BoundField
from django.forms.models import inlineformset_factory, BaseInlineFormSet
from django.forms.widgets import Textarea
from django.core.files.uploadedfile import UploadedFile
from django.utils import simplejson

from speeches.fields import FromStartIntegerField
from speeches.models import Speech, Speaker, Section, Recording, RecordingTimestamp, Tag
from speeches.widgets import AudioFileInput, BootstrapDateWidget, BootstrapTimeWidget
from speeches.utils import GroupedModelChoiceField

logger = logging.getLogger(__name__)

def add_class(f, cl):
    def class_tag(self, *args, **kwargs):
        kwargs.setdefault('attrs', {})['class'] = cl
        return f(self, *args, **kwargs)
    return class_tag

# For Bootstrap, which needs the label class, so monkey-patch
BoundField.label_tag = add_class(BoundField.label_tag, 'control-label')
# And make all textareas be block level 100% width
Textarea.render = add_class(Textarea.render, 'input-block-level')

class CleanAudioMixin(object):
    def clean_audio(self):
        audio = self.cleaned_data['audio']
        if audio and isinstance(audio, UploadedFile):
            ext = os.path.splitext(audio.name)[1]
            # Check that the file is an audio file and one of the
            # filetypes we can use
            if audio.content_type[0:6] != 'audio/' or ext not in ('.ogg', '.mp3', '.wav', '.3gp'):
                raise forms.ValidationError('That file does not appear to be an audio file')
        return audio

class SpeechAudioForm(forms.ModelForm, CleanAudioMixin):
    class Meta:
        model = Speech
        fields = ( 'audio', )
        widgets = {
            'audio': AudioFileInput,
        }

class SectionPickForm(forms.Form):
    section = forms.ModelChoiceField(label='Assign to section', queryset=Section.objects.all(), required=True)

class SpeechForm(forms.ModelForm, CleanAudioMixin):
    audio_filename = forms.CharField(widget=forms.HiddenInput, required=False)
    speaker = forms.ModelChoiceField(queryset=Speaker.objects.all(),
            empty_label = '',
            widget = Select2Widget(select2_options={ 'placeholder':'Choose a speaker', 'width': 'resolve' }),
            required=False)
    section = forms.ModelChoiceField(queryset=Section.objects.all(), required=False)
    start_date = forms.DateField(input_formats=['%d/%m/%Y'],
            widget=BootstrapDateWidget,
            required=False)
    start_time = forms.TimeField(input_formats=['%H:%M', '%H:%M:%S'],
            widget=BootstrapTimeWidget,
            required=False)
    end_date = forms.DateField(input_formats=['%d/%m/%Y'],
            widget=BootstrapDateWidget,
            required=False)
    end_time = forms.TimeField(input_formats=['%H:%M', '%H:%M:%S'],
            widget=BootstrapTimeWidget,
            required=False)
    #tags = TagField()
    tags = forms.ModelMultipleChoiceField(queryset=Tag.objects.all(),
            widget = Select2MultipleWidget(select2_options={ 'placeholder':'Choose tags', 'width': 'resolve' }),
            required=False)

    def clean(self):
        cleaned_data = self.cleaned_data
        if 'audio_filename' in cleaned_data and cleaned_data['audio_filename']:
            filename = cleaned_data['audio_filename']
            self.cleaned_data['audio'] = filename

        if not cleaned_data.get('text') and not cleaned_data.get('audio'):
            raise forms.ValidationError('You must provide either text or some audio')

        return cleaned_data

    def clean_start_time(self):
        if self.cleaned_data['start_time'] and not self.cleaned_data['start_date']:
            raise forms.ValidationError('If you provide a start time you must give a start date too')
        return self.cleaned_data['start_time']

    def clean_end_time(self):
        if self.cleaned_data['end_time'] and not self.cleaned_data['end_date']:
            raise forms.ValidationError('If you provide an end time you must give an end date too')
        return self.cleaned_data['end_time']

    class Meta:
        model = Speech
        widgets = {
            'audio': AudioFileInput,
            'event': forms.TextInput(),
            'title': forms.TextInput(),
            'location': forms.TextInput(),
            'source_url': forms.TextInput(),
        }
        exclude = ('celery_task_id', 'instance')

class RecordingAPIForm(forms.ModelForm, CleanAudioMixin):
    # Form for uploading a recording

    # Force timestamps to be a charfield so we can supply json to it
    timestamps = forms.CharField(required=False)

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        return super(RecordingAPIForm, self).__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = self.cleaned_data
        if 'audio_filename' in cleaned_data and cleaned_data['audio_filename']:
            filename = cleaned_data['audio_filename']
            self.cleaned_data['audio'] = filename
        return cleaned_data

    def clean_timestamps(self):
        # Allow uploading of timestamps which don't exist by turning the supplied
        # dictionary of timestamps into new RecordingTimestamp instances
        timestamps = []

        if not 'timestamps' in self.cleaned_data or not self.cleaned_data['timestamps']:
            return timestamps

        timestamps_json = simplejson.loads(self.cleaned_data['timestamps'])

        if not isinstance(timestamps_json, list):
            return timestamps

        for recording_timestamp in timestamps_json:
            try:
                if 'timestamp' in recording_timestamp:
                    # Note - we divide by 1000 because the time comes from javascript
                    # and is in milliseconds, but this expects the time in seconds
                    supplied_time = int(recording_timestamp['timestamp']/1000)
                    # We also make it a UTC time!
                    timestamp = datetime.utcfromtimestamp(supplied_time).replace(tzinfo=pytz.utc)
                    try:
                        speaker = Speaker.objects.get(pk=recording_timestamp['speaker'])
                    except:
                        speaker = None
                    timestamps.append(RecordingTimestamp(speaker=speaker, timestamp=timestamp, instance=self.request.instance))
                else:
                    # Timestamp is required
                    logger.error("No timestamp supplied in request: {0}".format(recording_timestamp))
                    pass
            except ValueError:
                # Ignore this one
                logger.error("ValueError encountered parsing: {0} into speaker/timestamp".format(recording_timestamp))


        if timestamps.count == 0:
            logger.error("Timestamps parameter was given but no timestamps parsed from: {0}".format(self.cleaned_data['timestamp']))

        return timestamps

    class Meta:
        model = Recording
        exclude = 'instance'

class RecordingForm(forms.ModelForm):
    class Meta:
        model = Recording
        exclude = ['instance', 'audio']

class SectionForm(forms.ModelForm):
    class Meta:
        model = Section
        exclude = 'instance'

class SpeakerForm(forms.ModelForm):
    class Meta:
        model = Speaker
        exclude = 'instance'
        widgets = {
            'name': forms.TextInput(),
        }

class SpeakerPopitForm(forms.Form):
    url = forms.URLField(label="PopIt URL")

class TimestampSecondsInput(forms.TextInput):

    first_timestamp = None

    def render(self, name, value, **kwargs):
        self.first_timestamp = self.first_timestamp or value
        delta = (value - self.first_timestamp).seconds
        return super(forms.TextInput, self).render(
            name, str(self.first_timestamp), **kwargs)


class RecordingTimestampForm(forms.ModelForm):
    timestamp = FromStartIntegerField()

    def __init__(self, *args, **kwargs):
        super(RecordingTimestampForm, self).__init__(*args, **kwargs)
        # Each timestamp needs to know the recording start time
        self.fields['timestamp'].recording_start = self.instance.recording.start_datetime

    class Meta:
        model = RecordingTimestamp
        exclude = ['instance','speech']
        widgets = {
            # 'timestamp': TimestampSecondsInput()
        }

class BaseRecordingTimestampFormSet(BaseInlineFormSet):
    def clean(self):
        if any(self.errors):
            return

        recording = self.instance

        first_timestamp = self.forms[0].cleaned_data['timestamp']
        last_timestamp = self.forms[-1].cleaned_data['timestamp']

        # TODO: check that first timestamp isn't before start of speech?  
        # or better to update speech start/end metadata if this happens?
        # NB: I'm assuming that first timestamp will always be aligned with
        # offset 0.  
        # The simplest thing is just to disallow changing the first
        # timestamp for now, and work out what the required semantics are
        # if any.

        if first_timestamp != recording.start_datetime:
            raise forms.ValidationError("Start time doesn't match recording start time!")

        # TODO: check that delta from first to last timestamp isn't longer
        # than length of audio
        # This is slightly complicated because we don't seem to cache this
        # metadata anywhere?  Might make sense to add to Recording?

        delta = (last_timestamp - first_timestamp).seconds
        if delta >= recording.audio_duration:
            raise forms.ValidationError('Difference between timestamps is too long for the uploaded audio')

        previous_timestamp = None
        for i in range(0, self.total_form_count()):
            form = self.forms[i]
            timestamp = form.cleaned_data['timestamp']
            if previous_timestamp:
                if timestamp <= previous_timestamp:
                    raise forms.ValidationError('Timestamps must be ordered')
            previous_timestamp = timestamp

RecordingTimestampFormSet = inlineformset_factory(
    Recording,
    RecordingTimestamp,
    formset = BaseRecordingTimestampFormSet,
    form = RecordingTimestampForm,
    extra = 0,
    can_delete = 0,
)
