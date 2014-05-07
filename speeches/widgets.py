from django.utils.html import escape, conditional_escape
from django.utils.safestring import mark_safe

from django.forms.widgets import ClearableFileInput, CheckboxInput, DateInput, TimeInput

class AudioFileInput(ClearableFileInput):
    pretty_input_start = u'<span class="button tiny secondary fileinput-button">Choose audio file'
    pretty_input_end = u'</span>'
    template_with_initial = u'%(initial_text)s: %(initial)s %(clear_template)s<br />%(input_text)s: %(pretty_input_start)s%(input)s%(pretty_input_end)s'
    template_with_clear = u'%(clear)s <label class="inline checkbox" for="%(clear_checkbox_id)s">%(clear_checkbox_label)s</label>'

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

class BootstrapDateWidget(DateInput):
    """
    A Widget that overrides the default date widget and styles it with Bootstrap
    """

    def __init__(self, attrs=None, format=None):
        super(BootstrapDateWidget, self).__init__(attrs, format)

    def render(self, name, value, attrs=None):
        """Override the output rendering to return a widget with some Bootstrap niceness"""

        # Set a placeholder attribute
        attrs['placeholder'] = 'dd/mm/yyyy'

        # Add a class attribute so that we can generically javascript things
        if 'class' in attrs:
            attrs['class'] = attrs['class'] + " datepicker"
        else:
            attrs['class'] = 'datepicker'

        widget = DateInput.render(self, name, value, attrs)

        return mark_safe(u'<div class="input-append datepicker">' + widget + '<span class="add-on"><i class="icon-calendar"></i></span></div>')

class BootstrapTimeWidget(TimeInput):
    """
    A Widget that overrides the default time widget and styles it with Bootstrap
    """

    def __init__(self, attrs=None, format=None):
        super(BootstrapTimeWidget, self).__init__(attrs, format)

    def render(self, name, value, attrs=None):
        """Override the output rendering to return a widget with some Bootstrap niceness"""

        # Set a placeholder attribute
        attrs['placeholder'] = 'hh:mm'

        widget = TimeInput.render(self, name, value, attrs)

        return mark_safe(u'<div class="input-append">' + widget + '<span class="add-on"><i class="icon-time"></i></span></div>')
