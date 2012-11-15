from django import forms

from speeches.models import Speech

class SpeechForm(forms.ModelForm):
    def clean(self):
        cleaned_data = self.cleaned_data
        if not cleaned_data.get('text') and not cleaned_data.get('audio'):
            raise forms.ValidationError('You must provide either text or some audio')
        return cleaned_data

    def clean_audio(self):
        audio = self.cleaned_data['audio']
        # Anything to do here?
        return audio

    class Meta:
        model = Speech
        widgets = {
            'text': forms.Textarea(attrs={'class': 'input-block-level'}),
            'event': forms.TextInput(),
            'title': forms.TextInput(),
            'location': forms.TextInput(),
            'speaker': forms.TextInput(),
            'source_url': forms.TextInput(),
        }
