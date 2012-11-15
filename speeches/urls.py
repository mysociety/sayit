from django.conf.urls import patterns, url

from speeches.views import SpeechCreate, SpeechView

urlpatterns = patterns('',
    url(r'^add$', SpeechCreate.as_view(), name='speech-add'),
    url(r'^(?P<pk>\d+)$', SpeechView.as_view(), name='speech-view'),
)

