from django.http import HttpResponse, HttpResponseRedirect
from django.utils import simplejson as json
from django.core.urlresolvers import reverse, reverse_lazy
from django.core import serializers
from django.conf import settings
from django.contrib import messages

from django.db.models import Count

from instances.views import InstanceFormMixin, InstanceViewMixin
from popit.models import ApiInstance

from speeches.forms import SpeechForm, SpeechAudioForm, SectionForm, RecordingAPIForm, SpeakerForm, SectionPickForm, SpeakerPopitForm
from speeches.models import Speech, Speaker, Section, Recording, Tag
import speeches.utils
from speeches.utils import AudioHelper, AudioException

from django.views.generic import View, CreateView, UpdateView, DetailView, ListView, RedirectView, FormView
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.edit import BaseFormView

import celery
import logging

logger = logging.getLogger(__name__)

class AddAnSRedirectView(RedirectView):
    url = '/%(path)s%(suffix)s'
    permanent = True
    query_string = True
    suffix = 's'

    def get_redirect_url(self, **kwargs):
        kwargs['suffix'] = self.suffix
        return super(AddAnSRedirectView, self).get_redirect_url(**kwargs)

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
        form.fields['section'].queryset = Section.objects.for_instance(self.request.instance).order_by('tree_id', 'lft')
        form.fields['speaker'].queryset = Speaker.objects.for_instance(self.request.instance)
        form.fields['tags'].queryset = Tag.objects.for_instance(self.request.instance)
        return form

class SpeechCreate(SpeechMixin, CreateView):
    def get_initial(self):
        initial = super(SpeechCreate, self).get_initial()
        initial = initial.copy()
        try:
            speaker = int(self.request.GET['speaker'])
        except:
            speaker = None
        if speaker:
            try:
                initial['speaker'] = Speaker.objects.get(pk=speaker)
            except Speaker.DoesNotExist:
                # Ignore the supplied speaker
                pass
        try:
            section = int(self.request.GET['section'])
        except:
            section = None
        if section:
            try:
                initial['section'] = Section.objects.get(pk=section)
            except Section.DoesNotExist:
                # Ignore the supplied section
                pass
        return initial

    def form_valid(self, form):
        resp = super(SpeechCreate, self).form_valid(form)

        # Now set off a Celery task to transcribe the audio for this speech
        self.object.start_transcribing()

        return resp

class SpeechUpdate(SpeechMixin, UpdateView):
    pass

class SpeechView(InstanceViewMixin, DetailView):
    model = Speech

    def get_queryset(self):
        return super(SpeechView, self).get_queryset().visible(self.request)

class SpeechList(InstanceViewMixin, ListView):
    model = Speech
    context_object_name = "speech_list"

    # The .annotate magic allows us to put things with a null start date
    # to the bottom of the list, otherwise they would naturally sort to the top
    def get_queryset(self):
        return super(SpeechList, self).get_queryset().visible(self.request).annotate(null_start_date=Count('start_date')).order_by("speaker__name", "-null_start_date", "-start_date", "-start_time")

class RecentSpeechList(InstanceViewMixin, ListView):
    model = Speech
    context_object_name = "recent_speeches"
    # Use a slightly different template
    template_name = "speeches/recent_speech_list.html"

    def get_queryset(self):
        return super(RecentSpeechList, self).get_queryset().visible(self.request).select_related('section', 'speaker').prefetch_related('tags').order_by("-created")[:50]

# This way around because of the 1.4 Django bugs with Mixins not calling super
class SpeakerView(InstanceViewMixin, ListView, SingleObjectMixin):
    model = Speaker
    paginate_by = 50
    template_name = 'speeches/speaker_detail.html'

    def get_queryset(self):
        queryset = super(SpeakerView, self).get_queryset()
        self.object = self.get_object(queryset)
        return self.object.speech_set.all().visible(self.request).select_related('section').prefetch_related('tags')

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        kwargs['speaker'] = self.object
        context = super(SpeakerView, self).get_context_data(**kwargs)
        return context

class SpeakerMixin(InstanceFormMixin):
    model = Speaker
    form_class = SpeakerForm

class SpeakerList(InstanceViewMixin, ListView):
    model = Speaker
    context_object_name = 'speaker_list'

class SpeakerCreate(SpeakerMixin, CreateView):
    pass

class SpeakerUpdate(SpeakerMixin, UpdateView):
    pass

class SpeakerPopit(InstanceFormMixin, FormView):
    template_name = 'speeches/speaker_popit.html'
    form_class = SpeakerPopitForm
    success_url = reverse_lazy('speaker-popit')

    def form_valid(self, form):
        ai, _ = ApiInstance.objects.get_or_create(url=form.cleaned_data['url'])
        ai.fetch_all_from_api()
        new = 0
        for person in ai.person_set.all():
            speaker, created = Speaker.objects.get_or_create(
                instance=self.request.instance,
                person=person,
                defaults={ 'name': person.name }
            )
            if created: new += 1

        messages.add_message(self.request, messages.SUCCESS, "PopIt instance added, %d new speakers added." % new)
        return super(SpeakerPopit, self).form_valid(form)

class SectionList(InstanceViewMixin, ListView):
    model = Section
    context_object_name = 'section_list'

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(SectionList, self).get_context_data(**kwargs)
        # Add in a QuerySet of all the speeches not in a section
        context['speech_list'] = Speech.objects.for_instance(self.request.instance).visible(self.request).filter(section=None).select_related('speaker').prefetch_related('tags')
        return context

class SectionMixin(InstanceFormMixin):
    model = Section
    form_class = SectionForm

    def get_form(self, form_class):
        form = super(SectionMixin, self).get_form(form_class)
        form.fields['parent'].queryset = Section.objects.for_instance(self.request.instance).order_by('tree_id', 'lft')
        return form

class SectionCreate(SectionMixin, CreateView):
    def get_initial(self):
        initial = super(SectionCreate, self).get_initial()
        initial = initial.copy()
        try:
            section = int(self.request.GET['section'])
        except:
            section = None
        if section:
            try:
                initial['parent'] = Section.objects.get(pk=section)
            except Section.DoesNotExist:
                # Ignore the supplied section
                pass
        return initial

class SectionUpdate(SectionMixin, UpdateView):
    pass

class SectionView(InstanceViewMixin, DetailView):
    model = Section

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(SectionView, self).get_context_data(**kwargs)
        # Add in a QuerySet of all the speeches in this section
        context['speech_list'] = kwargs['object'].speech_set.all().visible(self.request).select_related('speaker').prefetch_related('tags')
        return context

class BothObjectAndFormMixin(object):
    def get_context_data(self, **kwargs):
        context = super(BothObjectAndFormMixin, self).get_context_data(**kwargs)
        if 'object' not in context:
            context['object'] = self.get_object()
        if 'form' not in context:
            context['form'] = SectionPickForm()
        # Restrict to request's instance (can we think of a nicer way to do this?)
        context['form'].fields['section'].queryset = Section.objects.for_instance(self.request.instance).order_by('tree_id', 'lft')
        return context

class RecordingList(InstanceViewMixin, ListView):
    model = Recording

class RecordingDisplay(BothObjectAndFormMixin, InstanceViewMixin, DetailView):
    model = Recording

class RecordingSetSection(BothObjectAndFormMixin, InstanceFormMixin, FormView, SingleObjectMixin):
    template_name = 'speeches/recording_detail.html'
    form_class = SectionPickForm
    model = Recording

    def get_success_url(self):
        return self.object.get_absolute_url()

    def form_valid(self, form):
        self.object = self.get_object()
        num = self.object.add_speeches_to_section(form.cleaned_data['section'])
        messages.add_message(self.request, messages.SUCCESS, "Speeches assigned.")
        return super(RecordingSetSection, self).form_valid(form)

class RecordingView(View):
    def get(self, request, *args, **kwargs):
        view = RecordingDisplay.as_view()
        return view(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        view = RecordingSetSection.as_view()
        return view(request, *args, **kwargs)

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
