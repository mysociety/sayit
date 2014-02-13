from django import forms

from haystack.forms import SearchForm
from haystack.views import SearchView
from haystack.query import SearchQuerySet
from haystack.inputs import AutoQuery

from speeches.models import Speaker, Speech, Section

class HMSearchForm(SearchForm):
    def search(self):
        sqs = super(HMSearchForm, self).search()
        sqs = sqs.models(*self.model)
        sqs = sqs.highlight()
        return sqs

class SpeechForm(HMSearchForm):
    """
    A form with a hidden integer field that searches the speaker ID field
    """
    p = forms.IntegerField(required=False, widget=forms.HiddenInput())

    model = [ Speech, Section ]

    def search(self):
        sqs = super(SpeechForm, self).search()
        if self.is_valid() and self.cleaned_data.get('p'):
            sqs = sqs.filter(speaker=self.cleaned_data['p'])
            try:
                self.speaker = Speaker.objects.get(id=self.cleaned_data['p'])
            except:
                pass
        return sqs

class SpeakerForm(HMSearchForm):
    model = [ Speaker ]

class InstanceSearchView(SearchView):
    """
    A subclass that filters the search query set to speeches within the current
    request's instace.
    """
    def __init__(self, *args, **kwargs):
        kwargs['form_class'] = SpeechForm
        super(InstanceSearchView, self).__init__(*args, **kwargs)

    def build_form(self, *args, **kwargs):
        sqs = SearchQuerySet()
        sqs = sqs.narrow('instance:"%s"' % self.request.instance.label)
        self.searchqueryset = sqs
        return super(InstanceSearchView, self).build_form(*args, **kwargs)

    def extra_context(self):
        if not self.query:
            return {}

        self.form_class = SpeakerForm
        person_form = self.build_form()
        return {
            'speaker_results': person_form.search(),
        }
