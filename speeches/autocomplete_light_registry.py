import autocomplete_light
from speeches.models import Speaker

class SpeakerAutocomplete(autocomplete_light.AutocompleteModelBase):
    # Not sure if this messes up registration in some way as it can't find the
    # model any more, but it appears to work.
    @property
    def choices(self):
        if self.request:
            return Speaker.objects.for_instance(self.request.instance)
        return Speaker.objects.all()
    search_fields = ('name',)

autocomplete_light.register(SpeakerAutocomplete,
	autocomplete_js_attributes={'placeholder': 'Start typing a name...'})
