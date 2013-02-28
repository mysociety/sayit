from django.conf.urls import patterns, include, url

urlpatterns = patterns('django.views.generic.simple',
    (r'^', 'direct_to_template', {'template': 'instances/index.html'}),
)

