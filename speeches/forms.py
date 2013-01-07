import os
import logging

import autocomplete_light
autocomplete_light.autodiscover()

from django import forms
from django.forms.forms import BoundField
from django.core.files.uploadedfile import UploadedFile

from speeches.models import Speech, Speaker
from speeches.widgets import AudioFileInput, BootstrapDateWidget, BootstrapTimeWidget

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
            widget=autocomplete_light.ChoiceWidget('SpeakerAutocomplete'), 
            required=False)
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
        exclude = ('celery_task_id')

class SpeechAPIForm(forms.ModelForm, CleanAudioMixin):
    # A form like SpeechForm, but simpler, that is intended for use
    # like an api, eg: from mobile apps. See: speeches.views.SpeechAPICreate

    # Force speaker to be a CharField so we can supply popit_urls instead
    # of speaker ids
    speaker = forms.CharField(required=False)

    def clean(self):
        cleaned_data = self.cleaned_data
        if 'audio_filename' in cleaned_data and cleaned_data['audio_filename']:
            filename = cleaned_data['audio_filename']
            self.cleaned_data['audio'] = filename

        if not cleaned_data.get('text') and not cleaned_data.get('audio'):
            raise forms.ValidationError('You must provide either text or some audio')
        return cleaned_data

    # Look up the popit url in the db and return a speaker object id instead
    def clean_speaker(self):
        speaker_url = self.cleaned_data['speaker']
        speaker = None
        if speaker_url:
            try:
                speaker = Speaker.objects.get(popit_url=speaker_url)
            except Speaker.DoesNotExist:
                # TODO - lookup the speaker from the popit url somehow
                # Need to think about security and whether to do it right now
                # or save it in the db anyway and check asynchronously with the
                # populatespeakers management command
                logger.error('Speaker: {0} does not exist in db, setting to None'.format(speaker_url))
                speaker = None
        return speaker

    class Meta:
        model = Speech
        exclude = ('celery_task_id')
