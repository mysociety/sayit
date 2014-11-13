from haystack import indexes
from speeches.models import Speech, Speaker, Section


class SpeechIndex(indexes.SearchIndex, indexes.Indexable):
    # Use a template here to include speaker name as well... TODO
    text = indexes.CharField(document=True, model_attr='text')  # , use_template=True)
    title = indexes.CharField(model_attr='heading')  # use_template=True)
    start_date = indexes.DateTimeField(model_attr='start_date', null=True)
    instance = indexes.CharField(model_attr='instance__label')
    speaker = indexes.IntegerField(model_attr='speaker_id', null=True)

    def get_model(self):
        return Speech

    def index_queryset(self, using=None):
        return self.get_model()._default_manager.select_related('instance')

    def get_updated_field(self):
        return 'modified'


class SpeakerIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, model_attr='name')
    instance = indexes.CharField(model_attr='instance__label')

    def get_model(self):
        return Speaker

    def index_queryset(self, using=None):
        return self.get_model()._default_manager.select_related('instance')

    def get_updated_field(self):
        return 'updated_at'


class SectionIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, model_attr='heading')
    instance = indexes.CharField(model_attr='instance__label')

    def get_model(self):
        return Section

    def index_queryset(self, using=None):
        return self.get_model()._default_manager.select_related('instance')

    def get_updated_field(self):
        return 'modified'
