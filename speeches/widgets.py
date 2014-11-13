from django.utils.html import escape, conditional_escape
from django.utils.safestring import mark_safe
from django.utils import formats
from django.utils.translation import ugettext_lazy as _

from django.forms.widgets import ClearableFileInput, CheckboxInput, DateInput, TimeInput


class AudioFileInput(ClearableFileInput):
    pretty_input_start = u'<span class="button tiny secondary fileinput-button">Choose audio file'
    pretty_input_end = u'</span>'
    template_with_initial = u'%(initial_text)s: %(initial)s %(clear_template)s<br />' \
        u'%(input_text)s: %(pretty_input_start)s%(input)s%(pretty_input_end)s'
    template_with_clear = u'%(clear)s <label class="inline checkbox" for="%(clear_checkbox_id)s">' \
        u'%(clear_checkbox_label)s</label>'

    # Overridden whole function to provide nicer input button
    def render(self, name, value, attrs=None):
        substitutions = {
            'initial_text': self.initial_text,
            'input_text': self.input_text,
            'clear_template': '',
            'clear_checkbox_label': self.clear_checkbox_label,
            'pretty_input_start': self.pretty_input_start,
            'pretty_input_end': self.pretty_input_end,
        }
        template = u'%(pretty_input_start)s%(input)s%(pretty_input_end)s'
        substitutions['input'] = super(ClearableFileInput, self).render(name, value, attrs)

        if value and hasattr(value, "url"):
            template = self.template_with_initial
            substitutions['initial'] = (u'<audio src="%s" controls></audio>'
                                        % (escape(value.url),))
            if not self.is_required:
                checkbox_name = self.clear_checkbox_name(name)
                checkbox_id = self.clear_checkbox_id(checkbox_name)
                substitutions['clear_checkbox_name'] = conditional_escape(checkbox_name)
                substitutions['clear_checkbox_id'] = conditional_escape(checkbox_id)
                substitutions['clear'] = CheckboxInput().render(checkbox_name, False, attrs={'id': checkbox_id})
                substitutions['clear_template'] = self.template_with_clear % substitutions

        return mark_safe(template % substitutions)


# Make sure likely date placeholder texts are in the translation strings file.
_('yyyy-mm-dd')
_('dd/mm/yyyy')
_('dd/mm/yy')
_('mm/dd/yyyy')
_('mm/dd/yy')


class DatePickerWidget(DateInput):
    """A widget for replacing text input for dates with a date picker.

    An input with type=text is the default for a date in Django, and looks
    set to continue being for a while:
    https://code.djangoproject.com/ticket/16630#comment:11

    This widget replaces this with a foundation datepicker - details at
    http://foundation-datepicker.peterbeno.com/example.html
    """

    def render(self, name, value, attrs=None):
        """Extend the output to return a foundation-datepicker."""

        # Set a placeholder attribute - this should be the right thing
        # based on the locale which goes with your browser language
        # setting - so 'dd/mm/yyyy' for the UK
        date_format = (
            formats.get_format('DATE_INPUT_FORMATS')[0]
            .replace('%d', 'dd')
            .replace('%m', 'mm')
            .replace('%y', 'yy')
            .replace('%Y', 'yyyy')
            )

        attrs['placeholder'] = _(date_format)
        # We'll base the format for the date picker on a separate attribute
        # so that the placeholder can be translated.
        attrs['datepicker-format'] = date_format

        # Add a class attribute so that we can generically javascript things
        attrs['class'] = (attrs.get('class', '') + " fdatepicker").strip()

        return mark_safe(
            u'<div class="input-append">' +
            super(DatePickerWidget, self).render(name, value, attrs) +
            u'</div>'
            )


class TimePickerWidget(TimeInput):
    """A Widget for replacing text input for times.

    An input with type=text is the default for a time in Django, and looks
    set to continue being for a while:
    https://code.djangoproject.com/ticket/16630#comment:11

    This widget currently just sets a placeholder, but should probably
    replace this with a time picker of some sort.
    """

    def render(self, name, value, attrs=None):
        """Extend the output to include a placeholder."""

        # Set a placeholder attribute
        attrs['placeholder'] = _('hh:mm')

        return super(TimePickerWidget, self).render(name, value, attrs)
