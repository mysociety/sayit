import re
import sys

from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls import include, url
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.contrib.staticfiles import views as static_views
from django.contrib.auth import views as auth_views

# Admin section
from django.contrib import admin
admin.autodiscover()

urlpatterns = staticfiles_urlpatterns()
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# If we're running test, then we need to serve static files even though DEBUG
# is false to prevent lots of 404s. So do what staticfiles_urlpatterns would do.
if 'test' in sys.argv:
    static_url = re.escape(settings.STATIC_URL.lstrip('/'))
    urlpatterns += [
        url(r'^%s(?P<path>.*)$' % static_url, static_views.serve, {
            'insecure': True,
        }),
        url('^(?P<path>favicon\.ico)$', static_views.serve, {
            'insecure': True,
        }),
    ]

urlpatterns += [
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', include(admin.site.urls)),

    url(r'^accounts/login/$', auth_views.login, name='login'),
    url(r'^accounts/logout/$', auth_views.logout, {'next_page': '/'}, name='logout'),

    url(r'^', include('speeches.urls', app_name='speeches', namespace='speeches')),
]
