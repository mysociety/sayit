import datetime
from itertools import chain

from django import forms
from django.core import validators
from django.utils.encoding import force_text
from django.utils.safestring import mark_safe
from django.forms.utils import flatatt

from django_select2.widgets import Select2MultipleWidget

from speeches.models import Tag


# prepare_value() is called by a form before sending to the widget for display.
# clean() is called on form submission to validate it.
class FromStartIntegerField(forms.IntegerField):
    def __init__(self, *args, **kwargs):
        kwargs['min_value'] = 0
        super(FromStartIntegerField, self).__init__(*args, **kwargs)

    def prepare_value(self, value):
        if value in validators.EMPTY_VALUES:
            return None
        if isinstance(value, datetime.datetime):
            value = value - self.recording_start
            value = value.seconds + value.days * 86400
            value = int(value)
        return value

    def clean(self, value):
        value = super(FromStartIntegerField, self).clean(value)
        if value in validators.EMPTY_VALUES:
            return None
        # Get the number of seconds back to a datetime
        return datetime.timedelta(seconds=value) + self.recording_start


# This is the unfinished start of getting a Select2 tags:... element to work,
# so that you can add new tags within an edit form and have the server add them
# automatically. The client side below works, displaying the tags currently
# associated and allowing editing/adding, but server submission does not yet
# work. TagField needs to add any tags that aren't already present in the
# database.

class TagWidget(forms.SelectMultiple):
    def render(self, name, value, attrs=None, choices=()):
        if value is None:
            value = []
        final_attrs = self.build_attrs(attrs, type='text', name=name)

        value = set(force_text(v) for v in value)
        selected = []
        all_tags = []
        for option_value, option_label in chain(self.choices, choices):
            option_value = force_text(option_value)
            option_label = force_text(option_label)
            if option_value in value:
                selected.append(option_label)
            all_tags.append(option_label)

        self.options['tags'] = all_tags
        self.options['width'] = 'resolve'

        if selected:
            final_attrs['value'] = ','.join(selected)
        return mark_safe(u'<input%s />' % flatatt(final_attrs))


class TagWidgetMixin(Select2MultipleWidget, TagWidget):
    pass


class TagField(forms.ModelMultipleChoiceField):
    widget = TagWidgetMixin

    def __init__(self, *args, **kwargs):
        kwargs['required'] = False
        super(TagField, self).__init__(Tag, *args, **kwargs)

    def clean(self, value):
        # if value:
        #     value = [ item.strip() for item in value.split(",") ]
        return super(TagField, self).clean(value)
