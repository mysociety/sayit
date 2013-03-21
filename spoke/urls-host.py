from django.conf.urls import patterns, include

from tastypie.resources import ModelResource
from tastypie.api import Api

from instances.models import Instance

# Admin section
from django.contrib import admin
admin.autodiscover()

class InstanceResource(ModelResource):
    class Meta:
        queryset = Instance.objects.all()
        allowed_methods = [ 'get' ]
        excludes = [ 'id' ]
        include_resource_uri = False
        include_absolute_url = True
        detail_uri_name = 'label'
        filtering = { 'label': [ 'exact' ] }

v01_api = Api(api_name='v0.1')
v01_api.register(InstanceResource())

urlpatterns = patterns('',
    (r'^admin/doc/', include('django.contrib.admindocs.urls')),
    (r'^admin/', include(admin.site.urls)),

    (r'^accounts/login/$', 'django.contrib.auth.views.login'),
    (r'^accounts/logout/$', 'django.contrib.auth.views.logout'),
    (r'^accounts/tokens/?$', 'login_token.views.login_tokens_for_user'),
    (r'^accounts/mobile-login', 'login_token.views.check_login_token'),

    (r'^api/', include(v01_api.urls)),

    (r'^', include('instances.urls')),
)

