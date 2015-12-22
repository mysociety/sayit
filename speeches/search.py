from django import forms

from haystack.forms import SearchForm
from haystack.generic_views import SearchView
from haystack.query import SearchQuerySet

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

    model = [Speech, Section]

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
    model = [Speaker]


class InstanceSearchView(SearchView):
    """
    A subclass that filters the search query set to speeches within the current
    request's instace.
    """
    form_class = SpeechForm

    def get_queryset(self):
        sqs = SearchQuerySet()
        sqs = sqs.narrow('instance:"%s"' % self.request.instance.label)
        return sqs

    def get_context_data(self, **kwargs):
        context = super(InstanceSearchView, self).get_context_data(**kwargs)
        if kwargs.get('query'):
            person_form = self.get_form(SpeakerForm)
            context['speaker_results'] = person_form.search()

        return context
