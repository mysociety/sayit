import os

from django.conf import settings

def add_settings( request ):
    """Add some selected settings values to the context"""

    url = 'http://' + settings.BASE_HOST
    s = request.get_host().rsplit(':', 1)
    if len(s) == 2:
        url += ':' + s[1]

    return {
        'settings': {
            'GOOGLE_ANALYTICS_ACCOUNT': settings.GOOGLE_ANALYTICS_ACCOUNT,
            'DEBUG': settings.DEBUG,
            'BASE_HOST': url,
        }
    }

def nav_section(request):
    instance_about_page = False
    template = '%s/about/templates/about/%s/index.html' % (settings.PROJECT_ROOT, request.instance.label)
    if os.path.exists(template):
        instance_about_page = True
    return {
        'nav_primary': request.path_info.split('/')[1],
        'instance_about_page': instance_about_page,
    }
