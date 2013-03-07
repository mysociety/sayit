from django.http import HttpResponse, HttpResponseRedirect
from django.utils import simplejson as json
from django.core.urlresolvers import reverse
from django.core import serializers
from django.conf import settings

from django.db.models import Count

from instances.views import InstanceFormMixin, InstanceViewMixin

from speeches.forms import SpeechForm, SpeechAudioForm, SpeechAPIForm, MeetingForm, DebateForm, RecordingAPIForm
from speeches.models import Speech, Speaker, Meeting, Debate, Recording
import speeches.utils
from speeches.utils import AudioHelper, AudioException

from django.views.generic import CreateView, UpdateView, DetailView, ListView
from django.views.generic.edit import BaseFormView

import celery
import logging

logger = logging.getLogger(__name__)

class JSONResponseMixin(object):
    """Mixin for returning HTTPResponse of JSON data"""

    def render_to_response(self, context, **kwargs):
        kwargs['content_type'] = 'application/json'
        if not isinstance(context, basestring):
            context = json.dumps(context)
        location = kwargs.pop('location', None)
        response = HttpResponse(context, **kwargs)
        if location:
            response['Location'] = location
        return response

class SpeechAudioCreate(JSONResponseMixin, BaseFormView):
    form_class = SpeechAudioForm
    http_method_names = ['post']

    def form_valid(self, form):
        # The cleaned_data contains the TemporaryUploadedFile (File/UploadedFile subclass).
        # The form.instance contains the FieldFile with the magic save() we want.
        audio = form.cleaned_data['audio']
        form.instance.audio.save(audio.name, audio, save=False)
        return self.render_to_response({ 'status': 'done', 'filename': form.instance.audio.name })

    def form_invalid(self, form):
        return self.render_to_response({ 'error': form.errors['audio'] })

class SpeechMixin(InstanceFormMixin):
    model = Speech
    form_class = SpeechForm

    def get_form(self, form_class):
        form = super(SpeechMixin, self).get_form(form_class)
        form.fields['debate'].queryset = Debate.objects.for_instance(self.request.instance)
        form.fields['speaker'].queryset = Speaker.objects.for_instance(self.request.instance)
        return form

class SpeechCreate(SpeechMixin, CreateView):
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
        if "debate" in self.request.GET:
            try:
                initial['debate'] = Debate.objects.get(pk=self.request.GET["debate"])
            except Debate.DoesNotExist:
                # Ignore the supplied debate
                # TODO - would be good to tell the user that it doesn't exist but we need
                # to enable the messages module or similar to make it work
                pass
        return initial

    def form_valid(self, form):
        resp = super(SpeechCreate, self).form_valid(form)

        # Now set off a Celery task to transcribe the audio for this speech
        self.object.start_transcribing()

        return resp

# Api version of SpeechCreate
class SpeechAPICreate(InstanceFormMixin, JSONResponseMixin, CreateView):
    model = Speech
    form_class = SpeechAPIForm

    # Limit this view to POST requests, we don't want to show an HTML form for it
    http_method_names = ['post']

    def get_form(self, form_class):
        form = super(SpeechAPICreate, self).get_form(form_class)
        form.fields['debate'].queryset = Debate.objects.for_instance(self.request.instance)
        return form

    # Do as SpeechCreate does, but return a Location header instead of
    # redirecting to success_url
    def form_valid(self, form):
        super(SpeechAPICreate, self).form_valid(form)

        # Now set off a Celery task to transcribe the audio for this speech
        self.object.start_transcribing()

        # Return a 201

        # Serialise the object - annoyingly the second param must be an array or a QuerySet
        serialisable_fields = ('audio', 'title', 'text', 'created', 'modified', 'start',
            'end', 'source_url', 'speaker', 'location', 'event')
        serialised = serializers.serialize("json", [self.object], fields=serialisable_fields)
        # Now we need to massage this a bit because it's an array
        serialised = serialised[1:-1]

        return self.render_to_response(serialised, status=201, location=reverse("speech-view", args=[self.object.id]))

    def form_invalid(self, form):
        return self.render_to_response({ 'errors': json.dumps(form.errors) }, status=400)

class SpeechUpdate(SpeechMixin, UpdateView):
    pass

class SpeechView(InstanceViewMixin, DetailView):
    model = Speech

class SpeechList(InstanceViewMixin, ListView):
    model = Speech
    context_object_name = "speech_list"

    # The .annotate magic allows us to put things with a null start date
    # to the bottom of the list, otherwise they would naturally sort to the top
    def get_queryset(self):
        return super(SpeechList, self).get_queryset().annotate(null_start_date=Count('start_date')).order_by("speaker__name", "-null_start_date", "-start_date", "-start_time")

class RecentSpeechList(InstanceViewMixin, ListView):
    model = Speech
    context_object_name = "recent_speeches"
    # Use a slightly different template
    template_name = "speeches/recent_speech_list.html"

    def get_queryset(self):
        return super(RecentSpeechList, self).get_queryset().order_by("-created")[:50]

class SpeakerView(InstanceViewMixin, DetailView):
    model = Speaker

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(SpeakerView, self).get_context_data(**kwargs)
        # Add in a QuerySet of all the speeches by this speaker
        context['speech_list'] = Speech.objects.filter(speaker=kwargs['object'].id)
        return context

class MeetingCreate(InstanceFormMixin, CreateView):
    model = Meeting
    form_class = MeetingForm

class MeetingUpdate(InstanceFormMixin, UpdateView):
    model = Meeting
    form_class = MeetingForm

class MeetingView(InstanceViewMixin, DetailView):
    model = Meeting

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(MeetingView, self).get_context_data(**kwargs)
        # Add in a QuerySet of all the debates in this meeting
        context['debate_list'] = Debate.objects.filter(meeting=kwargs['object'].id)
        return context

class MeetingList(InstanceViewMixin, ListView):
    model = Meeting
    context_object_name = 'meeting_list'

    def get_queryset(self):
        return super(MeetingList, self).get_queryset().order_by("-created")

class DebateMixin(InstanceFormMixin):
    model = Debate
    form_class = DebateForm

    def get_form(self, form_class):
        form = super(DebateMixin, self).get_form(form_class)
        form.fields['meeting'].queryset = Meeting.objects.for_instance(self.request.instance)
        return form

class DebateCreate(DebateMixin, CreateView):
    def get_initial(self):
        initial = super(DebateCreate, self).get_initial()
        initial = initial.copy()
        if "meeting" in self.request.GET:
            try:
                initial['meeting'] = Meeting.objects.get(pk=self.request.GET["meeting"])
            except Meeting.DoesNotExist:
                # Ignore the supplied meeting
                # TODO - would be good to tell the user that it doesn't exist but we need
                # to enable the messages module or similar to make it work
                pass
        return initial

class DebateUpdate(DebateMixin, UpdateView):
    pass

class DebateView(InstanceViewMixin, DetailView):
    model = Debate

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(DebateView, self).get_context_data(**kwargs)
        # Add in a QuerySet of all the debates in this meeting
        context['speech_list'] = Speech.objects.filter(debate=kwargs['object'].id)
        return context

class RecordingView(InstanceViewMixin, DetailView):
    model = Recording

class RecordingAPICreate(InstanceFormMixin, JSONResponseMixin, CreateView):
    # View for RecordingAPIForm, to create a recording
    model = Recording
    form_class = RecordingAPIForm

    # Limit this view to POST requests, we don't want to show an HTML form for it
    http_method_names = ['post']

    success_url = 'DUMMY'

    def get_form_kwargs(self):
        kwargs = super(RecordingAPICreate, self).get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        logger.info("Processing recording")

        super(RecordingAPICreate, self).form_valid(form)

        # Create speeches from the recording
        speeches = Speech.objects.create_from_recording(self.object, self.request.instance)

        # Transcribe each speech
        for speech in speeches:
            speech.start_transcribing()

        # Return a 201 response
        serialisable_fields = ('audio', 'timestamps')
        serialised = serializers.serialize("json", [self.object], fields=serialisable_fields)
        serialised = serialised[1:-1]
        return self.render_to_response(serialised, status=201, location=reverse("recording-view", args=[self.object.id]))

    def form_invalid(self, form):
        return self.render_to_response({ 'errors': json.dumps(form.errors) }, status=400)
