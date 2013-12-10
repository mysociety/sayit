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
    return {
        'nav_primary': request.path_info.split('/')[1]
    }
