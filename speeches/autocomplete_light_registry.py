import autocomplete_light
from speeches.models import Speaker

autocomplete_light.register(Speaker, autocomplete_js_attributes={'placeholder': 'Start typing a name...'})