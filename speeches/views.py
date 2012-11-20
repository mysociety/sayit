from django.http import HttpResponse
from django.utils import simplejson as json

from speeches.forms import SpeechForm, SpeechAudioForm
from speeches.models import Speech
from django.views.generic import CreateView, UpdateView, DetailView, ListView
from django.views.generic.edit import BaseFormView

# Base as don't want template mixin. I find CBVs confusing :-/
class SpeechAudioCreate(BaseFormView):
    form_class = SpeechAudioForm

    def render_to_response(self, context, **kwargs):
        form = context.pop('form', None) # Don't care about the form
        data = json.dumps(context)
        kwargs['content_type'] = 'application/json'
        return HttpResponse(data, **kwargs)

    def form_valid(self, form):
        # The cleaned_data contains the TemporaryUploadedFile (File/UploadedFile subclass).
        # The form.instance contains the FieldFile which the magic save() we want.
        audio = form.cleaned_data['audio']
        form.instance.audio.save(audio.name, audio, save=False)
        return self.render_to_response({ 'status': 'done', 'filename': form.instance.audio.name })

    def form_invalid(self, form):
        return self.render_to_response({ 'error': form.errors['audio'] })

class SpeechCreate(CreateView):
    model = Speech
    form_class = SpeechForm

    def form_valid(self, form):
        # Do things with audio here...
        return super(SpeechCreate, self).form_valid(form)

class SpeechUpdate(UpdateView):
    model = Speech
    form_class = SpeechForm

class SpeechView(DetailView):
    model = Speech

class SpeechList(ListView):
    model = Speech
