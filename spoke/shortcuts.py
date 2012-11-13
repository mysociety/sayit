from django.shortcuts import render_to_response
from django.template import RequestContext

def render(request, template_name, context=None):
    if context is None: context = {}
    return render_to_response(template_name, context,
        context_instance = RequestContext(request)
    )
