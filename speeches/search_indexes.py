import datetime
from haystack import indexes
from speeches.models import Speech

class SpeechIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, model_attr='text') # , use_template=True)
    title = indexes.CharField() # use_template=True)
    start_date = indexes.DateTimeField()

    def get_model(self):
        return Speech

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects # .filter(pub_date__lte=datetime.datetime.now())
