import os
import logging
from datetime import datetime
import pytz

from django_select2.widgets import Select2Widget, Select2MultipleWidget
from mptt.forms import TreeNodeChoiceField

from django import forms
from django.forms.forms import BoundField
from django.core.files.uploadedfile import UploadedFile
from django.utils import simplejson

# from speeches.fields import TagField
from speeches.models import Speech, Speaker, Section, Recording, RecordingTimestamp, Tag
from speeches.widgets import AudioFileInput, BootstrapDateWidget, BootstrapTimeWidget
from speeches.utils import GroupedModelChoiceField

logger = logging.getLogger(__name__)

# For Bootstrap, which needs the label class, so monkey-patch
def add_class(f):
    def class_tag(self, contents=None, attrs=None):
        if attrs is None: attrs = {}
        attrs['class'] = 'control-label'
        return f(self, contents, attrs)
    return class_tag
BoundField.label_tag = add_class(BoundField.label_tag)

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

class SpeechForm(forms.ModelForm, CleanAudioMixin):
    audio_filename = forms.CharField(widget=forms.HiddenInput, required=False)
    speaker = forms.ModelChoiceField(queryset=Speaker.objects.all(),
            empty_label = '',
            widget = Select2Widget(select2_options={ 'placeholder':'Choose a speaker', 'width': 'resolve' }),
            required=False)
    section = TreeNodeChoiceField(queryset=Section.objects.all(), required=False)
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
            'text': forms.Textarea(attrs={'class': 'input-block-level'}),
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
                    timestamps.append(RecordingTimestamp.objects.create(speaker=speaker, timestamp=timestamp, instance=self.request.instance))
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


class SectionForm(forms.ModelForm):
    class Meta:
        model = Section
        exclude = 'instance'
