from django.conf.urls import patterns, url

from speeches.views import *

urlpatterns = patterns('',
    url(r'^$', SpeechList.as_view(), name='speech-list'),
    url(r'^/add$', SpeechCreate.as_view(), name='speech-add'),
    url(r'^/ajax_audio$', SpeechAudioCreate.as_view(), name='speech-ajax-audio'),
    url(r'^/(?P<pk>\d+)$', SpeechView.as_view(), name='speech-view'),
    url(r'^/(?P<pk>\d+)/edit$', SpeechUpdate.as_view(), name='speech-edit'),
)

