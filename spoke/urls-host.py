from django.conf.urls import patterns, include

from tastypie.resources import ModelResource
from tastypie.api import Api

from instances.models import Instance

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
    (r'^api/', include(v01_api.urls)),
    (r'^', include('instances.urls')),
)

