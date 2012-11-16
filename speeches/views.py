from speeches.forms import SpeechForm
from speeches.models import Speech
from django.views.generic import CreateView, UpdateView, DetailView, ListView

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
