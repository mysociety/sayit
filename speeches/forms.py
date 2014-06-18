import json
import os
import re
import logging
from datetime import datetime
import pytz

from django_select2.widgets import (
    Select2MultipleWidget, AutoHeavySelect2Widget,
    JSFunctionInContext, HeavySelect2Widget
    )
from django_select2.fields import AutoModelSelect2Field

from django.utils.translation import ugettext_lazy as _
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

from django.utils.encoding import force_text
from django import forms
from django.forms.forms import BoundField
from django.forms.models import inlineformset_factory, BaseInlineFormSet
from django.forms.widgets import Textarea
from django.forms.util import flatatt
from django.core.files.uploadedfile import UploadedFile

from speeches.fields import FromStartIntegerField
from speeches.models import Speech, Speaker, Section, Recording, RecordingTimestamp, Tag
from speeches.widgets import AudioFileInput, BootstrapDateWidget, BootstrapTimeWidget
from speeches.utils import GroupedModelChoiceField

logger = logging.getLogger(__name__)

def add_class(f, cl, attr_num):
    def class_tag(self, *args, **kwargs):
        if len(args) > attr_num:
            args[attr_num]['class'] = cl
        else:
            kwargs.setdefault('attrs', {})['class'] = cl
        return f(self, *args, **kwargs)
    return class_tag

# For Bootstrap, which needs the label class, so monkey-patch
BoundField.label_tag = add_class(BoundField.label_tag, 'control-label', 1)
# And make all textareas be block level 100% width
Textarea.render = add_class(Textarea.render, 'input-block-level', 2)

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

class SectionPickForm(forms.Form):
    section = forms.ModelChoiceField(label=_('Assign to section'), queryset=Section.objects.all(), required=True)

class Select2Widget(AutoHeavySelect2Widget):
    def __init__(self, *args, **kwargs):
        # AutoHeavySelect2Mixin's __init__ hard codes 'data_view' without giving
        # us the chance to add in the namespace we need. Let's hard code it
        # ourselves and then skip past AutoHeavySelect2Mixin in the MRO
        # to HeavySelect2Widget and continue from there.
        kwargs['data_view'] = "speeches:django_select2_central_json"

        HeavySelect2Widget.__init__(self, *args, **kwargs)

    def init_options(self):
        super(Select2Widget, self).init_options()
        self.options['createSearchChoice'] = JSFunctionInContext('django_select2.createSearchChoice')

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
            return data.getlist(name)

    def render(self, name, value, attrs=None, choices=()):
        """Because of the above; if we are given a list here, we don't want it."""
        if isinstance(value, list):
            value = value[0] if len(value) else None
        return super(Select2Widget, self).render(name, value, attrs, choices)

class StripWhitespaceField(forms.CharField):
    def clean(self, value):
        value = super(StripWhitespaceField, self).clean(value)
        if value:
            value = value.strip()
        return value

class CreateAutoModelSelect2Field(AutoModelSelect2Field):
    empty_values = [ None, '', [], (), {} ]

    # If anything tries to run a query on .queryset, it means we've missed
    # somewhere where we needed to limit things to the instance
    queryset = 'UNUSED'

    # instance will be set to an instance in the django-subdomain-instances
    # sense by the form
    instance = None

    def __init__(self, *args, **kwargs):
        self.search_fields = [ '%s__icontains' % self.column ]
        if 'widget' in kwargs or 'empty_label' in kwargs:
            logger.warn('widget/empty_label will be overwritten by using this field')
        kwargs['widget'] = Select2Widget(select2_options={ 'placeholder': ' ', 'width': '100%' })
        kwargs['empty_label'] = ''
        kwargs['required'] = kwargs.get('required', False)
        return super(CreateAutoModelSelect2Field, self).__init__(*args, **kwargs)

    def to_python(self, value):
        value = value.strip()

        # Inspiration from HeavyModelSelect2TagField
        if value in self.empty_values:
            return None
        try:
            key = self.to_field_name or 'pk'
            value = self.queryset.get(**{key: value})
        except (ValueError, self.model.DoesNotExist):
            # Note that value could currently arrive as two different things:
            # a stringified integer representing the id of an existing object, or
            # any other string representing the representative string of the object.
            value = self.queryset.create(**{ self.column: value, 'instance': self.instance })
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

class SpeakerField(CreateAutoModelSelect2Field):
    model = Speaker
    column = 'name'

class SectionField(CreateAutoModelSelect2Field):
    model = Section
    column = 'title'

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
    text = SpeechTextField(required=False)
    speaker = SpeakerField()
    section = SectionField()
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
    #tags = TagField()
    tags = forms.ModelMultipleChoiceField(queryset=Tag.objects.all(),
            widget = Select2MultipleWidget(select2_options={ 'placeholder':_('Choose tags'), 'width': 'resolve' }),
            required=False)

    def clean(self):
        cleaned_data = self.cleaned_data
        if 'audio_filename' in cleaned_data and cleaned_data['audio_filename']:
            filename = cleaned_data['audio_filename']
            self.cleaned_data['audio'] = filename

        if not cleaned_data.get('text') and not cleaned_data.get('audio'):
            raise forms.ValidationError(_('You must provide either text or some audio'))

        # If we have text but no speaker, then this should become a <narrative> element
        # in the Akoma Ntoso, which can't contain <p> elements, so we should replace any
        # in the middle with <br /> and get rid of the ones round the outside.
        if 'text' in cleaned_data and not cleaned_data.get('speaker'):
            text = cleaned_data['text']
            text = re.sub(r'</p>\n\n<p>', '<br />\n', text)
            text = re.sub(r'</?p>', '', text)
            cleaned_data['text'] = text

        return cleaned_data

    def clean_start_time(self):
        if self.cleaned_data['start_time'] and not self.cleaned_data.get('start_date'):
            raise forms.ValidationError(_('If you provide a start time you must give a start date too'))
        return self.cleaned_data['start_time']

    def clean_end_time(self):
        if self.cleaned_data['end_time'] and not self.cleaned_data['end_date']:
            raise forms.ValidationError(_('If you provide an end time you must give an end date too'))
        return self.cleaned_data['end_time']

    class Meta:
        model = Speech
        widgets = {
            'audio': AudioFileInput,
            'event': forms.TextInput(),
            'title': forms.TextInput(),
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
        # Allow uploading of timestamps which don't exist by turning the supplied
        # dictionary of timestamps into new RecordingTimestamp instances
        timestamps = []

        if not 'timestamps' in self.cleaned_data or not self.cleaned_data['timestamps']:
            logger.debug('No timestamps in cleaned_data')
            return timestamps

        logger.debug('timestamps received = %s' % self.cleaned_data['timestamps'])
        timestamps_json = json.loads(self.cleaned_data['timestamps'])

        if not isinstance(timestamps_json, list):
            return timestamps

        for recording_timestamp in timestamps_json:
            try:
                if 'timestamp' in recording_timestamp:
                    # Note - we divide by 1000 because the time comes from javascript
                    # and is in milliseconds, but this expects the time in seconds
                    supplied_time = int(recording_timestamp['timestamp']/1000)
                    # We also make it a UTC time!
                    timestamp = datetime.utcfromtimestamp(supplied_time).replace(tzinfo=pytz.utc)
                    try:
                        speaker = Speaker.objects.get(pk=recording_timestamp['speaker'])
                    except:
                        speaker = None
                    timestamps.append(RecordingTimestamp(speaker=speaker, timestamp=timestamp, instance=self.request.instance))
                else:
                    # Timestamp is required
                    logger.error("No timestamp supplied in request: {0}".format(recording_timestamp))
                    pass
            except ValueError:
                # Ignore this one
                logger.error("ValueError encountered parsing: {0} into speaker/timestamp".format(recording_timestamp))


        if timestamps.count == 0:
            logger.error("Timestamps parameter was given but no timestamps parsed from: {0}".format(self.cleaned_data['timestamp']))

        return timestamps

    class Meta:
        model = Recording
        exclude = ('instance',)

class RecordingForm(forms.ModelForm):
    class Meta:
        model = Recording
        exclude = ['instance', 'audio']

class SectionForm(forms.ModelForm):
    title = forms.CharField(required=True)
    parent = GroupedModelChoiceField(Section.objects.all(), 'parent', required=False)

    def __init__(self, *args, **kwargs):
        super(SectionForm, self).__init__(*args, **kwargs)
        if self.instance.id:
            ids = [ self.instance.id ]
            ids.extend( [ d.id for d in self.instance.get_descendants ] )
            self.fields['parent'].queryset = Section.objects.exclude(id__in=ids)

    class Meta:
        model = Section
        exclude = ('instance', 'slug')

    def clean_parent(self):
        parent = self.cleaned_data['parent']
        if self.instance and parent:
            if parent.id == self.instance.id:
                raise forms.ValidationError(_('Something cannot be its own parent'))
            descendant_ids = [ d.id for d in self.instance.get_descendants ]
            if parent.id in descendant_ids:
                raise forms.ValidationError(_('Something cannot have a parent that is also a descendant'))
        return parent

class SpeakerForm(forms.ModelForm):
    name = StripWhitespaceField()

    class Meta:
        model = Speaker
        exclude = ('instance', 'slug')

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
        exclude = ['instance','speech']

class BaseRecordingTimestampFormSet(BaseInlineFormSet):
    def clean(self):
        if any(self.errors):
            return

        recording = self.instance

        # we're using '_forms' to avoid clashing with forms import, e.g.
        # for ValidationError
        _forms = sorted(
            [ f for f in self.forms if 'timestamp' in f.cleaned_data ],
            key = lambda f: f.cleaned_data['timestamp']
        )

        first_timestamp = _forms[0].cleaned_data['timestamp']
        last_timestamp =  _forms[-1].cleaned_data['timestamp']

        # TODO: check that first timestamp isn't before start of speech?

        if first_timestamp < recording.start_datetime:
            raise forms.ValidationError(_("Start time is before recording start time!"))

        # TODO: check that delta from first to last timestamp isn't longer
        # than length of audio
        # This is slightly complicated because we don't seem to cache this
        # metadata anywhere?  Might make sense to add to Recording?

        delta = (last_timestamp - first_timestamp).seconds
        if delta >= recording.audio_duration:
            raise forms.ValidationError(_('Difference between timestamps is too long for the uploaded audio'))

        previous_timestamp = None
        for form in _forms:
            timestamp = form.cleaned_data['timestamp']
            if previous_timestamp:
                if timestamp <= previous_timestamp:
                    raise forms.ValidationError(_('Timestamps must be distinct'))
            previous_timestamp = timestamp

RecordingTimestampFormSet = inlineformset_factory(
    Recording,
    RecordingTimestamp,
    formset = BaseRecordingTimestampFormSet,
    form = RecordingTimestampForm,
    extra = 1,
    can_delete = 1,
)
