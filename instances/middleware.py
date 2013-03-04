import re

from django.conf import settings
from django.http import HttpResponseRedirect
from django.utils.cache import patch_vary_headers

from .models import Instance

class MultiInstanceMiddleware:
    def process_request(self, request):
        host = request.get_host().lower()
        domain = settings.BASE_HOST
        pattern = r'^(?P<instance>.*?)\.%s(?::(?P<port>.*))?$' % re.escape(domain)
        matches = re.match(pattern, host)
        if not matches:
            request.instance = None
            request.urlconf = 'instances.urls'
            return

        try:
            request.instance = Instance.objects.get(label=matches.group('instance'))
        except:
            url = 'http://' + settings.BASE_HOST
            if matches.group('port'):
                url += ':' + matches.group('port')
            return HttpResponseRedirect(url)

    def process_response(self, request, response):
        #if getattr(request, "urlconf", None):
        patch_vary_headers(response, ('Host',))
        return response

