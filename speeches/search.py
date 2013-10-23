from django import forms

from haystack.views import SearchView
from haystack.query import SearchQuerySet

class InstanceSearchView(SearchView):
    """
    A subclass that filters the search query set to speeches within the current
    request's instace.
    """
    def build_form(self, *args, **kwargs):
        sqs = SearchQuerySet()
        sqs = sqs.filter(instance=self.request.instance.label)
        self.searchqueryset = sqs
        return super(InstanceSearchView, self).build_form(*args, **kwargs)
