from django.conf.urls import patterns, url, include
from django.views.decorators.csrf import csrf_exempt

from speeches.views import *
from tastypie.api import Api
from speeches.api import SpeechResource, SpeakerResource

v01_api = Api(api_name='v0.1')
v01_api.register(SpeakerResource())
v01_api.register(SpeechResource())

urlpatterns = patterns('',
    url(r'^$', InstanceView.as_view(), name='home'),

    url(r'^(?P<path>speaker|recording)/?$', AddAnSRedirectView.as_view()),
    url(r'^(?P<path>speech)/?$', AddAnSRedirectView.as_view(suffix='es')),

    url(r'^speeches$', SpeechList.as_view(), name='speech-list'),
    url(r'^speech/add$', SpeechCreate.as_view(), name='speech-add'),
    url(r'^speech/ajax_audio$', SpeechAudioCreate.as_view(), name='speech-ajax-audio'),
    url(r'^speech/(?P<pk>\d+)$', SpeechView.as_view(), name='speech-view'),
    url(r'^speech/(?P<pk>\d+)/edit$', SpeechUpdate.as_view(), name='speech-edit'),

    url(r'^speakers$', SpeakerList.as_view(), name='speaker-list'),
    url(r'^speaker/add$', SpeakerCreate.as_view(), name='speaker-add'),
    url(r'^speaker/(?P<pk>\d+)$', SpeakerView.as_view(), name='speaker-view'),
    url(r'^speaker/(?P<pk>\d+)/edit$', SpeakerUpdate.as_view(), name='speaker-edit'),
    url(r'^speaker/popit$', SpeakerPopit.as_view(), name='speaker-popit'),

    url(r'^sections/(?P<pk>\d+)$', SectionView.as_view(), name='section-view'),
    url(r'^sections/add$', SectionCreate.as_view(), name='section-add'),
    url(r'^sections/(?P<pk>\d+)/edit$', SectionUpdate.as_view(), name='section-edit'),
    url(r'^sections$', SectionList.as_view(), name='section-list'),

    url(r'^recordings$', RecordingList.as_view(), name='recording-list'),
    url(r'^recording/(?P<pk>\d+)$', RecordingView.as_view(), name='recording-view'),
    url(r'^api/v0.1/recording/$', csrf_exempt(RecordingAPICreate.as_view()), name='recording-api-add'),

    url(r'^api/', include(v01_api.urls))
)

