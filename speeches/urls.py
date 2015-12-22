from django.conf.urls import url, include
from django.views.decorators.csrf import csrf_exempt

from speeches.views import (
    AddAnSRedirectView, SpeechAudioCreate, SpeechCreate, SpeechUpdate,
    SpeechDelete, SpeechView, SpeakerCreate, SpeakerUpdate, SpeakerDelete,
    SpeakerView, SpeakerList, SectionCreate, SectionUpdate, SectionDelete,
    SectionView, SectionViewAN, ParentlessList, RecordingList, RecordingView,
    RecordingUpdate, RecordingAPICreate, InstanceView, Select2AutoResponseView,
    PopoloImportView, AkomaNtosoImportView,
    )

from speeches.search import InstanceSearchView

try:
    from tastypie.api import NamespacedApi
    from speeches.api import SpeechResource, SpeakerResource, SectionResource
    # XXX The below assumes this app is being included with a 'speeches' namespace.
    # Unclear how to have this inherit whichever namespace is being used.
    v01_api = NamespacedApi(api_name='v0.1', urlconf_namespace='speeches')
    v01_api.register(SpeakerResource())
    v01_api.register(SpeechResource())
    v01_api.register(SectionResource())
except:
    v01_api = None

urlpatterns = [
    url(r'^$', InstanceView.as_view(), name='home'),

    # Override the usual AutoResponseView from django_select2 so as to limit
    # results by instance
    url(r"^select2/fields/auto.json$",
        Select2AutoResponseView.as_view(),
        name="django_select2_central_json"),

    url(r'^(?P<path>speaker|recording)/?$', AddAnSRedirectView.as_view()),
    url(r'^(?P<path>speech)/?$', AddAnSRedirectView.as_view(suffix='es')),

    url(r'^search/', InstanceSearchView.as_view(), name='haystack_search'),

    url(r'^speech/add$', SpeechCreate.as_view(), name='speech-add'),
    url(r'^speech/ajax_audio$', SpeechAudioCreate.as_view(), name='speech-ajax-audio'),
    url(r'^speech/(?P<pk>\d+)$', SpeechView.as_view(), name='speech-view'),
    url(r'^speech/(?P<pk>\d+)/edit$', SpeechUpdate.as_view(), name='speech-edit'),
    url(r'^speech/(?P<pk>\d+)/delete$', SpeechDelete.as_view(), name='speech-delete'),

    url(r'^speakers$', SpeakerList.as_view(), name='speaker-list'),
    url(r'^speaker/add$', SpeakerCreate.as_view(), name='speaker-add'),
    url(r'^speaker/(?P<pk>\d+)/edit$', SpeakerUpdate.as_view(), name='speaker-edit'),
    url(r'^speaker/(?P<pk>\d+)/delete$', SpeakerDelete.as_view(), name='speaker-delete'),
    url(r'^speaker/(?P<slug>.+)$', SpeakerView.as_view(), name='speaker-view'),

    url(r'^section/add$', SectionCreate.as_view(), name='section-add'),
    url(r'^section/(?P<pk>\d+)$', SectionView.as_view(), name='section-id-view'),
    url(r'^section/(?P<pk>\d+)/edit$', SectionUpdate.as_view(), name='section-edit'),
    url(r'^section/(?P<pk>\d+)/delete$', SectionDelete.as_view(), name='section-delete'),
    url(r'^speeches$', ParentlessList.as_view(), name='parentless-list'),

    url(r'^recordings$', RecordingList.as_view(), name='recording-list'),
    url(r'^recording/(?P<pk>\d+)$', RecordingView.as_view(), name='recording-view'),
    url(r'^recording/(?P<pk>\d+)/edit$', RecordingUpdate.as_view(), name='recording-edit'),
    url(r'^api/v0.1/recording/$', csrf_exempt(RecordingAPICreate.as_view()), name='recording-api-add'),

    url(r'^import/popolo', PopoloImportView.as_view(), name='import-popolo'),
    url(r'^import/akomantoso', AkomaNtosoImportView.as_view(), name='import-akoma-ntoso'),
]

if v01_api is not None:
    urlpatterns += [url(r'^api/', include(v01_api.urls))]

urlpatterns += [
    url(r'^(?P<full_slug>.+)\.an$', SectionViewAN.as_view(), name='section-view'),
    url(r'^(?P<full_slug>.+)$', SectionView.as_view(), name='section-view'),
]
