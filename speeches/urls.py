from django.conf.urls import patterns, url
from django.views.decorators.csrf import csrf_exempt

from speeches.views import *

urlpatterns = patterns('',
	url(r'^$', RecentSpeechList.as_view(), name='home'),
    url(r'^speeches$', SpeechList.as_view(), name='speech-list'),
    url(r'^speech/add$', SpeechCreate.as_view(), name='speech-add'),
    url(r'^speech/ajax_audio$', SpeechAudioCreate.as_view(), name='speech-ajax-audio'),
    url(r'^speech/(?P<pk>\d+)$', SpeechView.as_view(), name='speech-view'),
    url(r'^speech/(?P<pk>\d+)/edit$', SpeechUpdate.as_view(), name='speech-edit'),
    url(r'^speaker/(?P<pk>\d+)$', SpeakerView.as_view(), name='speaker-view'),
    url(r'^api/v0.1/speech/$', csrf_exempt(SpeechAPICreate.as_view()), name='speech-api-add'),
)

