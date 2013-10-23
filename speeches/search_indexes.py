import datetime
from haystack import indexes
from speeches.models import Speech

class SpeechIndex(indexes.SearchIndex, indexes.Indexable):
    # Use a template here to include speaker name as well... TODO
    text = indexes.CharField(document=True, model_attr='text') # , use_template=True)
    title = indexes.CharField() # use_template=True)
    start_date = indexes.DateTimeField(model_attr='start_date')
    instance = indexes.CharField(model_attr='instance__label')

    def get_model(self):
        return Speech

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects # .filter(pub_date__lte=datetime.datetime.now())
