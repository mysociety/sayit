from django import template
from django.template.defaultfilters import stringfilter
from django.utils.html import linebreaks
from django.utils.safestring import mark_safe, SafeData

import bleach
from django_bleach.templatetags.bleach_tags import bleach_args

register = template.Library()


@register.filter(needs_autoescape=True)
@stringfilter
def linebreaks_with_lead(value, autoescape=None):
    autoescape = autoescape and not isinstance(value, SafeData)
    out = linebreaks(value, autoescape)
    out = out.replace('<p>', '<p class="lead">', 1)
    return mark_safe(out)


@register.filter()
def striptags_highlight(value):
    bleached_value = bleach.clean(value, tags=['em'], strip=True)
    return mark_safe(bleached_value)


@register.filter('bleach')
def bleach_value(value):
    """Same as django_bleach, but convert the <br> we get back to valid XML,
    for the AN export."""
    bleached_value = bleach.clean(value, **bleach_args)
    bleached_value = bleached_value.replace('<br>', '<br/>')
    return mark_safe(bleached_value)
