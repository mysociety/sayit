from django.conf.urls import patterns, include, url
from django.views.generic import ListView

from instances.models import Instance

urlpatterns = patterns('',
    (r'^', ListView.as_view(
        queryset = Instance.objects.all(),
        context_object_name = 'instances',
        template_name = 'instances/index.html',
    )),
)

