import os

import autocomplete_light
autocomplete_light.autodiscover()

from django import forms
from django.forms.forms import BoundField
from django.core.files.uploadedfile import UploadedFile

from speeches.models import Speech, Speaker
from speeches.widgets import AudioFileInput

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
            if audio.content_type[0:6] != 'audio/' and ext not in ('.ogg', '.mp3'):
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
    speaker = forms.ModelChoiceField(queryset=Speaker.objects.all(), widget=autocomplete_light.ChoiceWidget('SpeakerAutocomplete'))

    def clean(self):
        cleaned_data = self.cleaned_data
        if 'audio_filename' in cleaned_data and cleaned_data['audio_filename']:
            filename = cleaned_data['audio_filename']
            self.cleaned_data['audio'] = filename

        if not cleaned_data.get('text') and not cleaned_data.get('audio'):
            raise forms.ValidationError('You must provide either text or some audio')
        return cleaned_data

    class Meta:
        model = Speech
        widgets = {
            'audio': AudioFileInput,
            'text': forms.Textarea(attrs={'class': 'input-block-level'}),
            'event': forms.TextInput(),
            'title': forms.TextInput(),
            'location': forms.TextInput(),
            'speaker': autocomplete_light.ChoiceWidget('SpeakerAutocomplete'),
            'source_url': forms.TextInput(),
        }
