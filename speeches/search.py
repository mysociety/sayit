from django import forms

from haystack.forms import SearchForm
from haystack.views import SearchView
from haystack.query import SearchQuerySet

class PersonSearchForm(SearchForm):
    """
    A form with a hidden integer field that searches the speaker ID field
    """
    p = forms.IntegerField(required=False, widget=forms.HiddenInput())

    def search(self):
        sqs = super(PersonSearchForm, self).search()
        if self.cleaned_data.get('p'):
            sqs = sqs.filter(speaker=self.cleaned_data['p'])
        return sqs

class InstanceSearchView(SearchView):
    """
    A subclass that filters the search query set to speeches within the current
    request's instace.
    """
    def __init__(self, *args, **kwargs):
        kwargs['form_class'] = PersonSearchForm
        super(InstanceSearchView, self).__init__(*args, **kwargs)

    def build_form(self, *args, **kwargs):
        sqs = SearchQuerySet()
        sqs = sqs.filter(instance=self.request.instance.label)
        self.searchqueryset = sqs
        return super(InstanceSearchView, self).build_form(*args, **kwargs)
