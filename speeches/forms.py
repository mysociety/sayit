import json
import os
import re
import logging
from datetime import datetime
import pytz

from django_select2.widgets import (
    Select2MultipleWidget, AutoHeavySelect2Widget,
    HeavySelect2Widget
    )
from django_select2.fields import AutoModelSelect2Field

from django.utils.translation import ugettext_lazy as _, ungettext
from django.utils.html import linebreaks

try:
    # Hack for Django 1.4 compatibility as remove_tags
    # wasn't invented yet.
    from django.utils.html import remove_tags

    def remove_p_and_br(value):
        return remove_tags(value, 'p br')

except ImportError:
    def remove_p_and_br(value):
        value = re.sub(r'</?p>', '', value)
        value = re.sub(r'<br ?/?>', '', value)
        return value

from django.utils.text import capfirst
from django.utils.encoding import force_text
from django import forms
from django.forms.models import inlineformset_factory, BaseInlineFormSet
from django.core.files.uploadedfile import UploadedFile

from speeches.fields import FromStartIntegerField
from speeches.models import (Speech, Speaker, Section,
                             Recording, RecordingTimestamp, Tag)
from speeches.widgets import AudioFileInput, DatePickerWidget, TimePickerWidget
from speeches.importers.import_popolo import PopoloImporter

logger = logging.getLogger(__name__)


def verbose_name(model, field):
    return capfirst(model._meta.get_field(field).verbose_name)


class CleanAudioMixin(object):
    def clean_audio(self):
        audio = self.cleaned_data['audio']
        if audio and isinstance(audio, UploadedFile):
            ext = os.path.splitext(audio.name)[1]
            # Check that the file is an audio file and one of the
            # filetypes we can use
            if (audio.content_type[0:6] != 'audio/' or
                    ext not in ('.ogg', '.mp3', '.wav', '.3gp')):
                raise forms.ValidationError(
                    'That file does not appear to be an audio file')
        return audio


class SpeechAudioForm(forms.ModelForm, CleanAudioMixin):
    class Meta:
        model = Speech
        fields = ('audio',)
        widgets = {
            'audio': AudioFileInput,
        }


class SectionPickForm(forms.Form):
    section = forms.ModelChoiceField(
        label=_('Assign to section'),
        queryset=Section.objects.all(),
        required=True,
        )


class Select2Widget(AutoHeavySelect2Widget):
    def __init__(self, *args, **kwargs):
        # AutoHeavySelect2Mixin's __init__ hard codes 'data_view' without
        # giving us the chance to add in the namespace we need. Let's
        # hard code it ourselves and then skip past
        # AutoHeavySelect2Mixin in the MRO to HeavySelect2Widget and
        # continue from there.
        kwargs['data_view'] = "speeches:django_select2_central_json"

        HeavySelect2Widget.__init__(self, *args, **kwargs)

    def value_from_datadict(self, data, files, name):
        # Inspiration from MultipleSelect2HiddenInput
        """We need to actually alter the form's self.data so that the form rendering
        works, as that's how the Select2 TagFields function. So always return
        the underlying list from the datadict."""

        # We want the value to always be a list when it's non-empty so that
        # below in the clean method on CreateAutoModelSelect2Field we can
        # change the value in place rather than replacing it.

        # If data is non-trivial and not a MultiValueDict, then an error will
        # be thrown, which is a good thing.
        if data:
            # Django 1.11 made getlist return a copy (#27198) which would break this,
            # so use its internal function in the absence of a larger refactor.
            if hasattr(data, '_getlist'):
                return data._getlist(name)
            else:
                return data.getlist(name)

    def render(self, name, value, attrs=None, choices=()):
        """Because of the above; if we are given a list here, we don't want it."""
        if isinstance(value, list):
            value = value[0] if len(value) else None
        return super(Select2Widget, self).render(name, value, attrs, choices)


class Select2CreateWidget(Select2Widget):
    """This widget is to allow someone to select an existing database entry,
    but also create a new one if needed."""
    def init_options(self):
        super(Select2Widget, self).init_options()
        # Version 4.3 of django-select2 changed, in
        # https://github.com/applegrew/django-select2/commit/36bac057, how
        # functions could be passed to the browser unaltered, using string
        # markers.
        self.options['createSearchChoice'] = '*START*django_select2.createSearchChoice*END*'


class StripWhitespaceField(forms.CharField):
    def clean(self, value):
        value = super(StripWhitespaceField, self).clean(value)
        if value:
            value = value.strip()
        return value


class CreateAutoModelSelect2Field(AutoModelSelect2Field):
    empty_values = [None, '', [], (), {}]

    # instance will be set to an instance in the django-subdomain-instances
    # sense by the form
    instance = None

    widget = Select2CreateWidget

    def __init__(self, *args, **kwargs):
        self.search_fields = ['%s__icontains' % self.column]
        if 'widget' in kwargs or 'empty_label' in kwargs:
            logger.warn(
                'widget/empty_label will be overwritten by using this field')
        kwargs['widget'] = self.widget(
            select2_options={'placeholder': ' ', 'width': '100%'})
        kwargs['empty_label'] = ''
        kwargs['required'] = kwargs.get('required', False)
        return (super(CreateAutoModelSelect2Field, self)
                .__init__(*args, **kwargs))

    def to_python(self, value):
        value = value.strip()

        # Inspiration from HeavyModelSelect2TagField
        if value in self.empty_values:
            return None
        try:
            key = self.to_field_name or 'pk'
            value = self.queryset.get(**{key: value})
        except (ValueError, self.model.DoesNotExist):
            value = self.create_model(value)
        return value

    def create_model(self, value):
        # Note that value could currently arrive as two different things:
        # 1) a stringified integer representing the id of an existing
        #    object, or
        # 2) any other string representing the representative string of
        #    the object.
        value = self.queryset.create(
            **{self.column: value, 'instance': self.instance})
        return value

    def clean(self, value):
        # Inspiration from HeavyModelSelect2TagField
        """We'll get a list here, due to the widget; we'll clean the first item,
        and be sure to alter the list that's been passed in. Because that list
        is used in any future render, and if we don't do it this way we get
        exceptions as it's not an integer..."""
        if value:
            v = value.pop()
            v = super(CreateAutoModelSelect2Field, self).clean(v)
            if v:
                value.append(v.pk)
                value = v
            else:
                value = None
        else:
            value = None

        return value


class NonCreateAutoModelSelect2Field(CreateAutoModelSelect2Field):
    widget = Select2Widget

    def create_model(self, value):
        raise forms.ValidationError(_('You must select an existing speaker'))


class SpeakerField(CreateAutoModelSelect2Field):
    model = Speaker
    column = 'name'


class NonCreateSpeakerField(NonCreateAutoModelSelect2Field):
    model = Speaker
    column = 'name'


class SectionField(CreateAutoModelSelect2Field):
    model = Section
    column = 'heading'


class NonCreateSectionField(NonCreateAutoModelSelect2Field):
    model = Section
    column = 'heading'


class SpeechTextFieldWidget(forms.Textarea):
    def render(self, name, value, attrs=None):
        # These first two steps are also done in the superclass, but it's
        # safe to repeat them here to get value to the right state.
        if value is None:
            value = ''
        value = force_text(value)
        value = re.sub(r'<br ?/?>', '<br />\n', value)
        value = remove_p_and_br(value)

        return super(SpeechTextFieldWidget, self).render(name, value, attrs)


class SpeechTextField(StripWhitespaceField):
    widget = SpeechTextFieldWidget

    def clean(self, value):
        value = super(SpeechTextField, self).clean(value)

        # It there is a value, and it's not already been HTMLified
        # then we want to use linebreaks to give it appropriate newlines.
        if value:
            if value.startswith('<p>'):
                value = re.sub(r'</p>\n*<p>', '</p>\n\n<p>', value)
            else:
                value = linebreaks(value)
        return value


class SpeechForm(forms.ModelForm, CleanAudioMixin):
    audio_filename = forms.CharField(widget=forms.HiddenInput, required=False)
    text = SpeechTextField(required=False, label=verbose_name(Speech, 'text'))
    speaker = SpeakerField(label=verbose_name(Speech, 'speaker'))
    section = SectionField(label=verbose_name(Speech, 'section'))

    type = forms.ChoiceField(
        label=verbose_name(Speech, 'type'),
        choices=Speech._meta.get_field('type').choices,
        widget=forms.HiddenInput, required=False,
        )

    start_date = forms.DateField(
        label=verbose_name(Speech, 'start_date'),
        widget=DatePickerWidget,
        required=False,
        localize=True,
        )
    start_time = forms.TimeField(
        input_formats=['%H:%M', '%H:%M:%S'],
        label=verbose_name(Speech, 'start_time'),
        widget=TimePickerWidget,
        required=False,
        )
    end_date = forms.DateField(
        label=verbose_name(Speech, 'end_date'),
        widget=DatePickerWidget,
        required=False,
        localize=True,
        )
    end_time = forms.TimeField(
        input_formats=['%H:%M', '%H:%M:%S'],
        label=verbose_name(Speech, 'end_time'),
        widget=TimePickerWidget,
        required=False,
        )
    # tags = TagField()
    tags = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.all(),
        label=verbose_name(Speech, 'tags'),
        widget=Select2MultipleWidget(
            select2_options={'placeholder': _('Choose tags'),
                             'width': 'resolve'}),
        required=False,
        )

    def clean(self):
        cleaned_data = self.cleaned_data

        # Temporary fix - see issue #340 (
        if not cleaned_data.get('type'):
            cleaned_data['type'] = ('speech' if cleaned_data.get('speaker')
                                    else 'narrative')

        if 'audio_filename' in cleaned_data and cleaned_data['audio_filename']:
            filename = cleaned_data['audio_filename']
            self.cleaned_data['audio'] = filename

        if not cleaned_data.get('text') and not cleaned_data.get('audio'):
            raise forms.ValidationError(
                _('You must provide either text or some audio'))

        # If we have text but no speaker, then this should become a
        # <narrative> element in the Akoma Ntoso, which can't contain
        # <p> elements, so we should replace any in the middle with
        # <br /> and get rid of the ones round the outside.
        if 'text' in cleaned_data and not cleaned_data.get('speaker'):
            text = cleaned_data['text']
            text = re.sub(r'</p>\n\n<p>', '<br />\n', text)
            text = re.sub(r'</?p>', '', text)
            cleaned_data['text'] = text

        return cleaned_data

    def clean_start_time(self):
        if (self.cleaned_data['start_time'] and
                not self.cleaned_data.get('start_date')):
            raise forms.ValidationError(
                _('If you provide a start time you must give a start date too')
                )
        return self.cleaned_data['start_time']

    def clean_end_time(self):
        if self.cleaned_data['end_time'] and not self.cleaned_data['end_date']:
            raise forms.ValidationError(
                _('If you provide an end time you must give an end date too'))
        return self.cleaned_data['end_time']

    class Meta:
        model = Speech
        widgets = {
            'audio': AudioFileInput,
            'event': forms.TextInput(),
            'heading': forms.TextInput(),
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
        # Allow uploading of timestamps which don't exist by turning
        # the supplied dictionary of timestamps into new
        # RecordingTimestamp instances
        timestamps = []

        if ('timestamps' not in self.cleaned_data or
                not self.cleaned_data['timestamps']):
            logger.debug('No timestamps in cleaned_data')
            return timestamps

        logger.debug(
            'timestamps received = %s' % self.cleaned_data['timestamps'])
        timestamps_json = json.loads(self.cleaned_data['timestamps'])

        if not isinstance(timestamps_json, list):
            return timestamps

        for recording_timestamp in timestamps_json:
            try:
                if 'timestamp' in recording_timestamp:
                    # Note - we divide by 1000 because the time comes
                    # from javascript and is in milliseconds, but this
                    # expects the time in seconds
                    supplied_time = int(recording_timestamp['timestamp'] / 1000)
                    # We also make it a UTC time!
                    timestamp = (datetime.utcfromtimestamp(supplied_time)
                                 .replace(tzinfo=pytz.utc))
                    try:
                        speaker = Speaker.objects.get(
                            pk=recording_timestamp['speaker'])
                    except:
                        speaker = None
                    timestamps.append(
                        RecordingTimestamp(
                            speaker=speaker,
                            timestamp=timestamp,
                            instance=self.request.instance)
                        )
                else:
                    # Timestamp is required
                    logger.error(
                        "No timestamp supplied in request: {0}".format(
                            recording_timestamp)
                        )
            except ValueError:
                # Ignore this one
                logger.error(
                    "ValueError encountered parsing: {0} into speaker/timestamp"
                    .format(recording_timestamp)
                    )

        if timestamps.count == 0:
            logger.error(
                "Timestamps parameter was given but no timestamps parsed from: {0}"
                .format(self.cleaned_data['timestamp'])
                )

        return timestamps

    class Meta:
        model = Recording
        exclude = ('instance',)


class RecordingForm(forms.ModelForm):
    class Meta:
        model = Recording
        exclude = ['instance', 'audio']


class SectionForm(forms.ModelForm):
    heading = forms.CharField(
        required=True,
        label=verbose_name(Section, 'heading'),
        )
    parent = NonCreateSectionField(label=verbose_name(Section, 'parent'))
    start_date = forms.DateField(
        label=verbose_name(Section, 'start_date'),
        widget=DatePickerWidget,
        required=False,
        localize=True,
        )
    start_time = forms.TimeField(
        input_formats=['%H:%M', '%H:%M:%S'],
        label=verbose_name(Section, 'start_time'),
        widget=TimePickerWidget,
        required=False,
        )
    source_url = forms.CharField(label=verbose_name(Section, 'source_url'), required=False)

    def __init__(self, *args, **kwargs):
        super(SectionForm, self).__init__(*args, **kwargs)
        if self.instance.id:
            ids = [self.instance.id]
            ids.extend([d.id for d in self.instance.get_descendants])
            self.fields['parent'].queryset = Section.objects.exclude(id__in=ids)

    class Meta:
        model = Section
        fields = ('heading', 'description', 'parent', 'source_url', 'start_date', 'start_time')

    def clean_parent(self):
        parent = self.cleaned_data['parent']
        if self.instance and parent:
            if parent.id == self.instance.id:
                raise forms.ValidationError(
                    _('Something cannot be its own parent'))
            descendant_ids = [d.id for d in self.instance.get_descendants]
            if parent.id in descendant_ids:
                raise forms.ValidationError(
                    _('Something cannot have a parent that is also a descendant')
                    )
        return parent


class SpeakerForm(forms.ModelForm):
    name = StripWhitespaceField(label=verbose_name(Speaker, 'name'))

    class Meta:
        model = Speaker
        fields = ('name', 'image', 'summary', 'sort_name')


class SpeakerDeleteForm(forms.ModelForm):
    new_speaker = NonCreateSpeakerField(
        label=_('New speaker'), required=False)

    def __init__(self, *args, **kwargs):
        super(SpeakerDeleteForm, self).__init__(*args, **kwargs)

        count = self.instance.speech_set.count()

        label = ungettext(
            "This speaker has %(count)d speech. What would you like to do with it?",
            "This speaker has %(count)d speeches. What would you like to do with them?",
            count
            ) % {'count': count}

        choices = (
            ('Reassign', ungettext('Assign it to another speaker', 'Assign them to another speaker', count)),
            ('Narrative', ungettext(
                'Make it into narrative (i.e. remove the speaker)',
                'Make them into narrative (i.e. remove the speaker)', count)),
            ('Delete', ungettext('Delete it', 'Delete them', count)),
            )

        self.fields['action'] = forms.ChoiceField(
            label=label,
            choices=choices,
            widget=forms.RadioSelect(),
            )

    def clean(self):
        super(SpeakerDeleteForm, self).clean()
        new_speaker = self.cleaned_data.get('new_speaker')

        if self.cleaned_data.get('action') == 'Reassign':
            if new_speaker and new_speaker.id == self.instance.id:
                self._errors['new_speaker'] = self.error_class(
                    [_("You can't assign speeches to the speaker you're deleting")]
                    )
            if not new_speaker and 'new_speaker' not in self._errors:
                # When Django 1.7 is our oldest supported version, we can use add_error
                # https://docs.djangoproject.com/en/1.7/ref/forms/api/#django.forms.Form.add_error
                self._errors['new_speaker'] = self.error_class(
                    [_('You must choose a new speaker if reassigning speeches')]
                    )
        else:
            if new_speaker:
                # As above when our oldest supported version of Django is 1.7
                self._errors['new_speaker'] = self.error_class(
                    [_('You must not choose a new speaker unless reassigning speeches')]
                    )
        return self.cleaned_data

    class Meta:
        model = Speaker
        fields = ('id',)


class RecordingTimestampForm(forms.ModelForm):
    timestamp = FromStartIntegerField()

    def __init__(self, *args, **kwargs):
        super(RecordingTimestampForm, self).__init__(*args, **kwargs)
        # Each timestamp needs to know the recording start time if it
        # is bound (e.g. not an extra, blank field)
        if self.instance.recording_id:
            self.fields['timestamp'].recording_start = self.instance.recording.start_datetime

    def save(self, commit=True):
        self.instance.instance_id = self.instance.recording.instance_id
        return super(RecordingTimestampForm, self).save(commit)

    class Meta:
        model = RecordingTimestamp
        exclude = ['instance', 'speech']


class BaseRecordingTimestampFormSet(BaseInlineFormSet):
    def clean(self):
        if any(self.errors):
            return

        recording = self.instance

        # we're using '_forms' to avoid clashing with forms import, e.g.
        # for ValidationError
        _forms = sorted(
            [f for f in self.forms if 'timestamp' in f.cleaned_data],
            key=lambda f: f.cleaned_data['timestamp']
        )

        first_timestamp = _forms[0].cleaned_data['timestamp']
        last_timestamp = _forms[-1].cleaned_data['timestamp']

        # TODO: check that first timestamp isn't before start of speech?

        if first_timestamp < recording.start_datetime:
            raise forms.ValidationError(
                _("Start time is before recording start time!"))

        # TODO: check that delta from first to last timestamp isn't longer
        # than length of audio
        # This is slightly complicated because we don't seem to cache this
        # metadata anywhere?  Might make sense to add to Recording?

        delta = (last_timestamp - first_timestamp).seconds
        if delta >= recording.audio_duration:
            raise forms.ValidationError(
                _('Difference between timestamps is too long for the uploaded audio'))

        previous_timestamp = None
        for form in _forms:
            timestamp = form.cleaned_data['timestamp']
            if previous_timestamp:
                if timestamp <= previous_timestamp:
                    raise forms.ValidationError(
                        _('Timestamps must be distinct'))
            previous_timestamp = timestamp


RecordingTimestampFormSet = inlineformset_factory(
    Recording,
    RecordingTimestamp,
    formset=BaseRecordingTimestampFormSet,
    form=RecordingTimestampForm,
    extra=1,
    can_delete=1,
)


class PopoloImportForm(forms.Form):
    location = forms.URLField(
        label=_('Location of Popolo JSON data'))

    def __init__(self, instance=None, *args, **kwargs):
        super(PopoloImportForm, self).__init__(*args, **kwargs)
        self.instance = instance

    def clean(self):
        cleaned_data = super(PopoloImportForm, self).clean()

        cleaned_data['importer'] = PopoloImporter(
            cleaned_data['location'],
            instance=self.instance,
            )

        return cleaned_data


class AkomaNtosoImportForm(forms.Form):
    location = forms.URLField(label=_('Location of Akoma Ntoso data'))

    def __init__(self, instance=None, *args, **kwargs):
        super(AkomaNtosoImportForm, self).__init__(*args, **kwargs)
        self.instance = instance

        if Section.objects.filter(instance=instance).exists():
            self.fields['existing_sections'] = forms.ChoiceField(
                label=_('What would you like to do with existing top level sections?'),
                choices=(
                    ('skip', _('Skip them - keep them exactly as they are')),
                    ('replace', _('Replace them - throw away the existing data and use the new')),
                    ('merge', _('Merge the new data into the existing sections - things in both will be duplicated')),
                    ),
                widget=forms.RadioSelect(),
                )
