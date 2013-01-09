from django.http import HttpResponse, HttpResponseRedirect
from django.utils import simplejson as json
from django.core.urlresolvers import reverse
from django.core import serializers
from django.conf import settings

from django.db.models import Count

from speeches.forms import SpeechForm, SpeechAudioForm, SpeechAPIForm, MeetingForm
from speeches.models import Speech, Speaker, Meeting
from speeches.tasks import transcribe_speech
import speeches.util

from django.views.generic import CreateView, UpdateView, DetailView, ListView
from django.views.generic.edit import BaseFormView

import celery
import logging

logger = logging.getLogger(__name__)

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
        # The form.instance contains the FieldFile with the magic save() we want.
        audio = form.cleaned_data['audio']
        form.instance.audio.save(audio.name, audio, save=False)
        return self.render_to_response({ 'status': 'done', 'filename': form.instance.audio.name })

    def form_invalid(self, form):
        return self.render_to_response({ 'error': form.errors['audio'] })

class SpeechCreate(CreateView):
    model = Speech
    form_class = SpeechForm

    def get_initial(self):
        initial = super(SpeechCreate, self).get_initial()
        initial = initial.copy()
        if "speaker" in self.request.GET:
            try:
                initial['speaker'] = Speaker.objects.get(pk=self.request.GET["speaker"])
            except Speaker.DoesNotExist:
                # Ignore the supplied speaker
                # TODO - would be good to tell the user that they don't exist but we need
                # to enable the messages module or similar to make it work
                pass
            return initial

    def form_valid(self, form):
        # Do things with audio here...

        # First save the form - we can't let the super-class do it because
        # we need to add some stuff to the object afterwards
        self.object = form.save()

        # Now set off a Celery task to transcribe the audio for this speech
        speeches.util.start_transcribing_speech(self.object)
        
        return HttpResponseRedirect(self.get_success_url())

# Api version of SpeechCreate
class SpeechAPICreate(CreateView):
    model = Speech
    form_class = SpeechAPIForm

    # Limit this view to POST requests, we don't want to show an HTML form for it
    http_method_names = ['post']

    # Return JSON - context should already be serialized JSON
    def render_to_response(self, context, **kwargs):
        kwargs['content_type'] = 'application/json'
        return HttpResponse(context, **kwargs)

    # Do as SpeechCreate does, but return a Location header instead of
    # redirecting to success_url
    def form_valid(self, form):
        # Do things with audio here...

        # First save the form - we can't let the super-class do it because
        # we need to add some stuff to the object afterwards
        self.object = form.save()

        # Now set off a Celery task to transcribe the audio for this speech
        speeches.util.start_transcribing_speech(self.object)

        # Return a 201

        # Serialise the object - annoyingly the second param must be an array or a QuerySet
        serialisable_fields = ('audio', 'title', 'text', 'created', 'modified', 'start',
            'end', 'source_url', 'speaker', 'location', 'event')
        serialised = serializers.serialize("json", [self.object], fields=serialisable_fields, use_natural_keys=True)
        # Now we need to massage this a bit because it's an array
        serialised = serialised[1:-1]

        response = self.render_to_response(serialised)
        response.status_code = 201
        response['Location'] = reverse("speech-view", args=[self.object.id])
        return response

    def form_invalid(self, form):
        response = self.render_to_response(json.dumps({ 'errors': json.dumps(form.errors) }))
        response.status_code = 400
        return response

class SpeechUpdate(UpdateView):
    model = Speech
    form_class = SpeechForm

class SpeechView(DetailView):
    model = Speech

class SpeechList(ListView):
    model = Speech
    context_object_name = "speech_list"
    # The .annotate magic allows us to put things with a null start date
    # to the bottom of the list, otherwise they would naturally sort to the top
    queryset = Speech.objects.all().annotate(null_start_date=Count('start_date')).order_by("speaker__name", "-null_start_date", "-start_date", "-start_time")

class RecentSpeechList(ListView):
    model = Speech
    context_object_name = "recent_speeches"
    # Get the first 50 speeches only
    queryset = Speech.objects.all().order_by("-created")[:50]
    # Use a slightly different template
    template_name = "speeches/recent_speech_list.html"
   
    # Add an extra variable to the template for the site info
    # TODO: Get this from a config table in the db or something like that
    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(RecentSpeechList, self).get_context_data(**kwargs)
        context['site_title'] = settings.SITE_TITLE
        return context

class SpeakerView(DetailView):
    model = Speaker

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(SpeakerView, self).get_context_data(**kwargs)
        # Add in a QuerySet of all the speeches by this speaker
        context['speech_list'] = Speech.objects.filter(speaker=kwargs['object'].id)
        return context

class MeetingCreate(CreateView):
    model = Meeting
    form_class = MeetingForm

class MeetingUpdate(UpdateView):
    model = Meeting
    form_class = MeetingForm

class MeetingView(DetailView):
    model = Meeting
