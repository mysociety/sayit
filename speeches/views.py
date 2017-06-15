import datetime
import json
from six import string_types

from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse, reverse_lazy, resolve
from django.core import serializers
from django.contrib import messages
from django.forms import Form
from django.forms.forms import NON_FIELD_ERRORS
from django.template import loader

from django.utils.html import strip_tags
from django.utils.translation import ugettext as _, ungettext

from django.db.models import Count, Avg
from django.db.models.functions import Length
from django.shortcuts import get_object_or_404

from instances.views import InstanceFormMixin, InstanceViewMixin

from speeches.forms import (
    SpeechForm, SpeechAudioForm, SectionForm,
    RecordingAPIForm, SpeakerForm, SectionPickForm,
    RecordingTimestampFormSet, SpeakerDeleteForm,
    PopoloImportForm, AkomaNtosoImportForm,
    )
from speeches.models import Speech, Speaker, Section, Recording, Tag
from speeches.mixins import Base32SingleObjectMixin, UnmatchingSlugException
from speeches.importers.import_akomantoso import ImportAkomaNtoso

from django.views.generic import (
    View, CreateView, UpdateView, DeleteView, DetailView, ListView,
    RedirectView, FormView,
    )
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.edit import BaseFormView, BaseUpdateView

from django_select2.views import AutoResponseView

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
        if not isinstance(context, string_types):
            context = json.dumps(context)
        location = kwargs.pop('location', None)
        response = HttpResponse(context, **kwargs)
        if location:
            response['Location'] = location
        return response


class NamespaceMixin(object):
    """Mixin for adding current_app based on namespace"""

    def reverse(self, template, **kwargs):
        self.request.current_app = resolve(self.request.path).namespace
        return reverse(template, **kwargs)

    def reverse_lazy(self, template, **kwargs):
        self.request.current_app = resolve(self.request.path).namespace
        return reverse_lazy(template, **kwargs)

    def render_to_response(self, context, **kwargs):
        self.request.current_app = resolve(self.request.path).namespace
        return super(NamespaceMixin, self).render_to_response(context, **kwargs)


class SpeechAudioCreate(JSONResponseMixin, BaseFormView):
    form_class = SpeechAudioForm
    http_method_names = ['post']

    def form_valid(self, form):
        # The cleaned_data contains the TemporaryUploadedFile
        # (File/UploadedFile subclass). The form.instance contains the
        # FieldFile with the magic save() we want.
        audio = form.cleaned_data['audio']
        form.instance.audio.save(audio.name, audio, save=False)
        return self.render_to_response(
            {'status': 'done', 'filename': form.instance.audio.name})

    def form_invalid(self, form):
        return self.render_to_response({'error': form.errors['audio']})


class SpeechMixin(NamespaceMixin, InstanceFormMixin):
    model = Speech
    form_class = SpeechForm

    def get_form(self, form_class=None):
        form = super(SpeechMixin, self).get_form(form_class)

        form.fields['section'].queryset = Section.objects.for_instance(self.request.instance)
        form.fields['speaker'].queryset = Speaker.objects.for_instance(self.request.instance)
        form.fields['tags'].queryset = Tag.objects.for_instance(self.request.instance)

        # Instance in the sense of https://github.com/mysociety/django-subdomain-instances
        form.fields['speaker'].instance = self.request.instance
        form.fields['section'].instance = self.request.instance

        return form


class SpeechDelete(SpeechMixin, DeleteView):
    def get_success_url(self):
        return self.reverse('speeches:parentless-list')


class SpeechCreate(SpeechMixin, CreateView):
    def get_context_data(self, **kwargs):
        context = super(SpeechCreate, self).get_context_data(**kwargs)
        added = self.request.GET.get('added', None)
        section = self.request.GET.get('section', None)
        if added and section:
            section_object = Section.objects.get(pk=section)
            if section_object:
                context['added'] = added
                context['section'] = section_object
        return context

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
                section_object = Section.objects.get(pk=section)
                initial['section'] = section_object

                # default things to last speech in section
                try:
                    speech = section_object.speech_set.reverse()[0]

                    # Basic data is just defaulted from the last speech
                    initial['location'] = speech.location
                    initial['heading'] = speech.heading
                    initial['event'] = speech.event
                    initial['public'] = speech.public
                    initial['source_url'] = speech.source_url

                    # For speaker, to make it simpler to transcribe a dialogue
                    # between A -> B -> A -> B we default to the speaker of the
                    # *penultimate* speech, if that exists, or latest one
                    # otherwise.
                    if not speaker:
                        try:
                            penultimate_speech = section_object.speech_set.reverse()[1]
                            initial['speaker'] = penultimate_speech.speaker
                        except IndexError:
                            initial['speaker'] = speech.speaker

                    # We attempt to do vaguely clever things with the end or
                    # start time of previous speech.
                    if speech.end_date:
                        speech_end_datetime = datetime.datetime.combine(
                            speech.end_date, speech.end_time or datetime.time(0, 0))
                        if speech.end_time:
                            if speech.start_date and speech.start_time:
                                speech_start_datetime = datetime.datetime.combine(
                                    speech.start_date, speech.start_time)
                                if speech_start_datetime == speech_end_datetime:
                                    speech_end_datetime = speech_end_datetime + datetime.timedelta(seconds=1)
                            initial['start_time'] = speech_end_datetime.time()
                        initial['start_date'] = speech_end_datetime.date()
                    elif speech.start_date:
                        if speech.start_time:
                            speech_start_datetime = datetime.datetime.combine(speech.start_date, speech.start_time)
                            speech_start_datetime = speech_start_datetime + datetime.timedelta(seconds=10)
                            initial['start_time'] = speech_start_datetime.time()
                            initial['start_date'] = speech_start_datetime.date()
                        else:
                            initial['start_date'] = speech.start_date

                except IndexError:
                    # don't attempt to default anything
                    pass

            except Section.DoesNotExist:
                # Ignore the supplied section
                pass
        return initial

    def get_success_url(self):
        return "{}?created".format(self.object.get_absolute_url())

    def form_valid(self, form):
        resp = super(SpeechCreate, self).form_valid(form)

        # Now set off a Celery task to transcribe the audio for this speech
        self.object.start_transcribing()

        if 'add_another' in self.request.POST:
            url = self.reverse('speeches:speech-add')
            speech = self.object
            if speech.section_id:
                url = url + '?section=%d&added=%d' % (speech.section_id, speech.id)
            return HttpResponseRedirect(url)
        else:
            return resp


class SpeechUpdate(SpeechMixin, UpdateView):
    pass


class SpeechView(NamespaceMixin, InstanceViewMixin, DetailView):
    model = Speech

    def get_queryset(self):
        return super(SpeechView, self).get_queryset().visible(self.request)

    def get_context_data(self, **kwargs):
        context = super(SpeechView, self).get_context_data(**kwargs)
        context['title'] = strip_tags(
            self.object.title or
            u'\u201C%s\u201D' % self.object.summary
            )
        return context


class InstanceView(NamespaceMixin, InstanceViewMixin, ListView):
    """Done as a ListView on Speech to get recent speeches, we get instance for
    free in the request."""
    model = Speech
    paginate_by = 20

    # Use a slightly different template
    def get_template_names(self):
        return [
            "speeches/%s/home.html" % self.request.instance.label,
            "speeches/home.html"
        ]

    def get_context_data(self, **kwargs):
        context = super(InstanceView, self).get_context_data(**kwargs)
        context['count_speeches'] = Speech.objects.for_instance(self.request.instance).visible(self.request).count()
        context['count_sections'] = Section.objects.for_instance(self.request.instance).count()
        context['count_speakers'] = Speaker.objects.for_instance(self.request.instance).count()
        context['average_length'] = Speech.objects.for_instance(self.request.instance) \
            .annotate(length=Length('text')).aggregate(avg=Avg('length'))['avg']
        return context


# It doesn't actually use base32 IDs in the URL, but this works around Django
# 1.4 generic view bug, and allows non-canonical slug redirects to Just Work.
class SpeakerView(NamespaceMixin, InstanceViewMixin, Base32SingleObjectMixin, ListView):
    model = Speaker
    paginate_by = 50
    template_name = 'speeches/speaker_detail.html'
    slug_field = 'slugs__slug'

    def get_queryset(self):
        queryset = super(SpeakerView, self).get_queryset()
        self.object = self.get_object(queryset)
        return self.object.speech_set.all().visible(self.request) \
            .select_related('section', 'speaker').prefetch_related('tags').reverse()

    def get_context_data(self, **kwargs):
        kwargs['speech_list'] = self.object_list
        context = super(SpeakerView, self).get_context_data(**kwargs)
        context['section_count'] = self.object.speech_set.all().visible(self.request) \
            .aggregate(Count('section', distinct=True))['section__count']
        context['longest_speech'] = self.object.speech_set.annotate(length=Length('text')).order_by('-length')[:1]
        context['title'] = _('View Speaker: %(speaker_name)s') % {'speaker_name': self.object.name}
        return context


class SpeakerMixin(NamespaceMixin, InstanceFormMixin):
    model = Speaker
    form_class = SpeakerForm


class SpeakerList(NamespaceMixin, InstanceViewMixin, ListView):
    model = Speaker
    context_object_name = 'speaker_list'


class SpeakerCreate(SpeakerMixin, CreateView):
    pass


class SpeakerUpdate(SpeakerMixin, UpdateView):
    pass


class SpeakerDeleteNoSpeechesMixin(object):
    def delete(self):
        self.object.delete()
        return HttpResponseRedirect(self.get_success_url())

    def post(self, request, *args, **kwargs):
        if self.object.speech_set.exists():
            return super(SpeakerDeleteNoSpeechesMixin, self).post(request, *args, **kwargs)
        else:
            return self.delete()


class SpeakerDelete(SpeakerMixin, BaseUpdateView, SpeakerDeleteNoSpeechesMixin, FormView):
    form_class = SpeakerDeleteForm
    template_name = 'speeches/speaker_delete.html'

    def get_success_url(self):
        return self.reverse('speeches:speaker-list')

    def get_form(self, form_class=None):
        if self.object.speech_set.exists():
            form = super(SpeakerDelete, self).get_form(form_class)
            form.fields['new_speaker'].queryset = Speaker.objects.for_instance(self.request.instance)
            form.fields['new_speaker'].instance = self.request.instance
        else:
            form = Form

        return form

    def form_valid(self, form):
        action = form.cleaned_data['action']

        if action == 'Delete':
            Speech.objects.filter(speaker=self.object).delete()
        elif action == 'Narrative':
            # This, and reassignment below, will need to use a queue at scale
            for s in Speech.objects.filter(speaker=self.object):
                s.type = 'narrative'
                s.save()
        elif action == 'Reassign':
            for s in Speech.objects.filter(speaker=self.object):
                s.speaker = form.cleaned_data['new_speaker']
                s.save()

        return self.delete()


class ParentlessList(NamespaceMixin, InstanceViewMixin, ListView):
    model = Speech
    template_name = 'speeches/parentless_list.html'
    paginate_by = 50

    def get_queryset(self):
        qs = super(ParentlessList, self).get_queryset()
        qs = qs.visible(self.request)
        qs = qs.filter(section=None)
        qs = qs.select_related('speaker').prefetch_related('tags')
        return qs

    def get_context_data(self, **kwargs):
        context = super(ParentlessList, self).get_context_data(**kwargs)

        # Add in a QuerySet of all the sections without a parent
        context['section_list'] = Section.objects.for_instance(self.request.instance).filter(parent=None)
        return context


class SectionMixin(NamespaceMixin, InstanceFormMixin):
    model = Section
    form_class = SectionForm

    def get_form(self, form_class=None):
        form = super(SectionMixin, self).get_form(form_class)
        form.fields['parent'].queryset = Section.objects.for_instance(self.request.instance)
        form.fields['parent'].instance = self.request.instance
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


class SectionDelete(SectionMixin, DeleteView):
    def get_success_url(self):
        return self.reverse('speeches:parentless-list')


class SectionView(NamespaceMixin, InstanceViewMixin, DetailView):
    model = Section

    def get(self, request, *args, **kwargs):
        try:
            return super(SectionView, self).get(request, *args, **kwargs)
        except UnmatchingSlugException as e:
            return HttpResponseRedirect(e.args[0])

    def get_object(self, queryset=None):
        pk = self.kwargs.get(self.pk_url_kwarg, None)
        if pk is not None:
            return super(SectionView, self).get_object(queryset)
        full_slug = self.kwargs.get('full_slug', None)
        slugs = full_slug.split('/')
        parent = None
        for i, slug in enumerate(slugs):
            obj = get_object_or_404(self.model, instance=self.request.instance, slugs__slug=slug, parent=parent)
            if slug != obj.slug:
                new_url = obj.get_absolute_url()
                if i < len(slugs) - 1:
                    new_url += '/' + '/'.join(slugs[i + 1:])
                raise UnmatchingSlugException(new_url)
            parent = obj
        return obj

    def get_context_data(self, **kwargs):
        all_speeches = kwargs.pop('all_speeches', False)
        # Call the base implementation first to get a context
        context = super(SectionView, self).get_context_data(**kwargs)
        # Add in a QuerySet of all the speeches in this section
        context['section_tree'] = kwargs['object'].get_descendants_tree_with_speeches(
            self.request,
            all_speeches=all_speeches,
        )
        context['title'] = _('View Section: %(section_title)s') % {'section_title': self.object.title}
        context['speech_template'] = loader.get_template('speeches/speech.html')
        return context


class SectionViewAN(SectionView):
    template_name = 'speeches/section_detail.an'

    def render_to_response(self, context, **response_kwargs):
        response_kwargs['content_type'] = 'text/xml'
        return super(SectionView, self).render_to_response(context, **response_kwargs)

    def get_context_data(self, **kwargs):
        kwargs['all_speeches'] = True
        context = super(SectionViewAN, self).get_context_data(**kwargs)
        speakers = set(
            s[0].speaker
            for s in context['section_tree']
            if isinstance(s[0], Speech) and s[0].speaker
        )
        context['speakers'] = speakers
        context['server_name'] = self.request.META.get('SERVER_NAME')
        return context


class BothObjectAndFormMixin(object):
    def get_context_data(self, **kwargs):
        context = super(BothObjectAndFormMixin, self).get_context_data(**kwargs)
        if 'object' not in context:
            context['object'] = self.get_object()
        if 'form' not in context:
            context['form'] = SectionPickForm()
        # Restrict to request's instance (can we think of a nicer way to do this?)
        context['form'].fields['section'].queryset = Section.objects.for_instance(self.request.instance)
        return context


class RecordingList(NamespaceMixin, InstanceViewMixin, ListView):
    model = Recording


class RecordingDisplay(NamespaceMixin, BothObjectAndFormMixin, InstanceViewMixin, DetailView):
    model = Recording


class RecordingSetSection(NamespaceMixin, BothObjectAndFormMixin, InstanceFormMixin, FormView, SingleObjectMixin):
    template_name = 'speeches/recording_detail.html'
    form_class = SectionPickForm
    model = Recording

    def get_success_url(self):
        return self.object.get_absolute_url()

    def form_valid(self, form):
        self.object = self.get_object()
        self.object.add_speeches_to_section(form.cleaned_data['section'])
        messages.add_message(self.request, messages.SUCCESS, _("Speeches assigned."))
        return super(RecordingSetSection, self).form_valid(form)


class RecordingView(NamespaceMixin, View):
    def get(self, request, *args, **kwargs):
        view = RecordingDisplay.as_view()
        return view(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        view = RecordingSetSection.as_view()
        return view(request, *args, **kwargs)


# NB: this is not an UpdateView, at least for now, as it only updates
# RecordingTimestamp not the actual Recording class.
class RecordingUpdate(NamespaceMixin, InstanceFormMixin, DetailView):
    model = Recording
    template_name_suffix = "_form"

    def get_context_data(self, **kwargs):
        context = super(RecordingUpdate, self).get_context_data(**kwargs)
        context['recordingtimestamp_formset'] = RecordingTimestampFormSet(
            self.request.POST or None, instance=self.object)
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)  # Sigh
        recordingtimestamp_formset = context['recordingtimestamp_formset']

        recording = self.object

        for form in recordingtimestamp_formset:
            # in case we are processing any extra fields, which don't have
            # this set already
            form.fields['timestamp'].recording_start = recording.start_datetime

        if recordingtimestamp_formset.is_valid():
            recordingtimestamp_formset.save()

            recording.create_or_update_speeches(self.request.instance)

            # then delete the associated speeches, as Django can't
            # infer a cascade here
            for form in recordingtimestamp_formset.deleted_forms:
                try:
                    form.instance.speech.delete()
                except:
                    logger.info("Timestamp isn't linked to speech")

            return HttpResponseRedirect(recording.get_absolute_url())
        return self.render_to_response(context)


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
        logger.info("  " + repr(form.cleaned_data))

        super(RecordingAPICreate, self).form_valid(form)

        recording = self.object

        recording_timestamps = form.cleaned_data.get('timestamps', [])
        for recording_timestamp in recording_timestamps:
            recording_timestamp.recording = recording
            recording_timestamp.save()

        if len(recording_timestamps):
            recording.start_datetime = recording_timestamps[0].timestamp
            recording.save()

        # Create speeches from the recording
        speeches = recording.create_or_update_speeches(self.request.instance)

        # Transcribe each speech
        for speech in speeches:
            speech.start_transcribing()

        # Return a 201 response
        serialisable_fields = ('audio', 'timestamps')
        serialised = serializers.serialize(
            "json", [recording], fields=serialisable_fields)
        serialised = serialised[1:-1]

        return self.render_to_response(
            serialised,
            status=201,
            location=reverse("speeches:recording-view", args=[recording.id]),
            )

    def form_invalid(self, form):
        return self.render_to_response(
            {'errors': json.dumps(form.errors)},
            status=400,
            )


class Select2AutoResponseView(AutoResponseView):
    def check_all_permissions(self, request, *args, **kwargs):
        super(Select2AutoResponseView, self).check_all_permissions(request, *args, **kwargs)

        try:
            id = int(request.GET['object_id'])
        except:
            id = None

        model = request._AutoResponseView__django_select2_local.model
        qs = model.objects.for_instance(request.instance)
        if id:
            qs = qs.exclude(id=id)
        request._AutoResponseView__django_select2_local.queryset = qs


class PopoloImportView(NamespaceMixin, InstanceFormMixin, FormView):
    template_name = 'speeches/popolo_import_form.html'
    form_class = PopoloImportForm

    def get_success_url(self):
        return self.reverse('speeches:speaker-list')

    def get_form_kwargs(self):
        kwargs = super(PopoloImportView, self).get_form_kwargs()
        kwargs['instance'] = self.request.instance
        return kwargs

    def form_valid(self, form):
        results = form.cleaned_data['importer'].import_persons()

        created = results['created']
        refreshed = results['refreshed']

        if created or refreshed:
            messages.add_message(
                self.request,
                messages.SUCCESS if created else messages.INFO,
                ' '.join((
                    ungettext(
                        "%(created)d speaker created.",
                        "%(created)d speakers created.",
                        created,
                        ) % {'created': created},
                    ungettext(
                        "%(refreshed)d speaker refreshed.",
                        "%(refreshed)d speakers refreshed.",
                        refreshed,
                        ) % {'refreshed': refreshed},
                    ))
                )

        else:
            messages.add_message(
                self.request,
                messages.WARNING,
                _('No speakers found.'),
                )

        return super(PopoloImportView, self).form_valid(form)


class AkomaNtosoImportView(NamespaceMixin, InstanceFormMixin, FormView):
    template_name = 'speeches/akoma_ntoso_import_form.html'
    form_class = AkomaNtosoImportForm

    def get_success_url(self):
        return self.reverse('speeches:home')

    def get_form_kwargs(self):
        kwargs = super(AkomaNtosoImportView, self).get_form_kwargs()
        kwargs['instance'] = self.request.instance
        return kwargs

    def form_valid(self, form):
        try:
            importer = ImportAkomaNtoso(
                instance=self.request.instance,
                commit=True,
                clobber=form.cleaned_data.get('existing_sections'),
                )

            stats = importer.import_document(form.cleaned_data['location'])
        except:
            form._errors[NON_FIELD_ERRORS] = form.error_class(
                [_('Sorry - something went wrong with the import')])
            return self.form_invalid(form)

        speakers = stats.get(Speaker, 0)
        sections = stats.get(Section, 0)
        speeches = stats.get(Speech, 0)
        success = speakers or sections or speeches

        if success:
            messages.add_message(
                self.request,
                messages.SUCCESS,
                _('Created: ') + ', '.join(
                    (
                        ungettext(
                            "%(speakers)d speaker",
                            "%(speakers)d speakers",
                            speakers,
                            ) % {'speakers': speakers},
                        ungettext(
                            "%(sections)d section",
                            "%(sections)d sections",
                            sections,
                            ) % {'sections': sections},
                        ungettext(
                            "%(speeches)d speech",
                            "%(speeches)d speeches",
                            speeches,
                            ) % {'speeches': speeches},
                        )
                    )
                )
        else:
            messages.add_message(
                self.request,
                messages.INFO,
                _('Nothing new to import.'),
                )

        return super(AkomaNtosoImportView, self).form_valid(form)
