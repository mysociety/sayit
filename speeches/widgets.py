from django.utils.html import escape, conditional_escape
from django.utils.safestring import mark_safe

from django.forms.widgets import ClearableFileInput, CheckboxInput

class AudioFileInput(ClearableFileInput):
    pretty_input_start = u'<span class="btn fileinput-button"> <i class="icon-plus"></i> <span>Choose audio file</span>'
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

