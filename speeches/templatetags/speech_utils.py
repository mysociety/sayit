from django import template
from django.template.defaultfilters import stringfilter
from django.utils.html import linebreaks
from django.utils.safestring import mark_safe, SafeData

register = template.Library()

@register.filter(needs_autoescape=True)
@stringfilter
def linebreaks_with_lead(value, autoescape=None):
    autoescape = autoescape and not isinstance(value, SafeData)
    out = linebreaks(value, autoescape)
    out = out.replace('<p>', '<p class="lead">', 1)
    return mark_safe(out)
