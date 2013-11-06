import datetime
from haystack import indexes
from speeches.models import Speech

class SpeechIndex(indexes.SearchIndex, indexes.Indexable):
    # Use a template here to include speaker name as well... TODO
    text = indexes.CharField(document=True, model_attr='text') # , use_template=True)
    title = indexes.CharField() # use_template=True)
    start_date = indexes.DateTimeField(model_attr='start_date', null=True)
    instance = indexes.CharField(model_attr='instance__label')
    speaker = indexes.IntegerField(model_attr='speaker__id', null=True)
    sections = indexes.MultiValueField()


    def prepare_sections(self, obj):
        # Add the ids of all the sections up to the top parent. Intention is to
        # make it easy to search all speeches under a given section.
        section = obj.section
        section_ids = []

        # TODO this recursion is very inefficient, should refactor
        while section:
            section_ids.append(section.id)
            section = section.parent

        return section_ids


    def get_model(self):
        return Speech

    def index_queryset(self, using=None):
        """Used when the entire index for model is updated."""
        return self.get_model().objects # .filter(pub_date__lte=datetime.datetime.now())
