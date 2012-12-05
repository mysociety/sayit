import re
import sys

from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls import patterns, include, url
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

import autocomplete_light
autocomplete_light.autodiscover()

# Admin section
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', 'spoke.views.home', name='home'),

    url(r'^', include('speeches.urls')),

    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', include(admin.site.urls)),

    url(r'autocomplete/', include('autocomplete_light.urls')),
)

urlpatterns += staticfiles_urlpatterns()
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# If we're running test, then we need to serve static files even though DEBUG
# is false to prevent lots of 404s. So do what staticfiles_urlpatterns would do.
if 'test' in sys.argv:
    static_url = re.escape(settings.STATIC_URL.lstrip('/'))
    urlpatterns += patterns('',
        url(r'^%s(?P<path>.*)$' % static_url, 'django.views.static.serve', {
            'document_root': settings.STATIC_ROOT,
        }),
        url('^(?P<path>favicon\.ico)$', 'django.views.static.serve', {
            'document_root': settings.STATIC_ROOT,
        }),
    )

