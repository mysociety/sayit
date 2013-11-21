# Create your views here.

from django.views.generic.base import TemplateView
from django.http import Http404
from django.template import TemplateDoesNotExist
from django.template.loader import get_template

class AboutView(TemplateView):
    def get_template_names(self):
        slug = self.kwargs.get('slug')
        if not slug: raise Http404
        if self.request.instance:
            name = 'about/%s/%s.html' % (self.request.instance.label, slug)
        else:
            name = 'about/%s.html' % slug
        try:
            get_template(name)
        except TemplateDoesNotExist:
            raise Http404
        return name
