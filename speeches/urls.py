from django.conf.urls import patterns, url

from speeches.views import SpeechCreate, SpeechView, SpeechList

urlpatterns = patterns('',
    url(r'^$', SpeechList.as_view(), name='speech-list'),
    url(r'^/add$', SpeechCreate.as_view(), name='speech-add'),
    url(r'^/(?P<pk>\d+)$', SpeechView.as_view(), name='speech-view'),
)

