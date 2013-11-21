from django.conf.urls import patterns, url, include

from about.views import *

urlpatterns = patterns('',
    (r'^$', AboutView.as_view(), { 'slug': 'index' }),
    (r'^/(?P<slug>.+)$', AboutView.as_view()),
)

