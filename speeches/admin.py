from django.contrib import admin
from django.db import models

from speeches.models import Speaker, Speech, Tag
from speeches.widgets import AudioFileInput

class SpeechAdmin(admin.ModelAdmin):
    formfield_overrides = {
        models.FileField: { 'widget': AudioFileInput },
    }

admin.site.register(Speaker)
admin.site.register(Speech, SpeechAdmin)
admin.site.register(Tag)

# class FooBarAdmin(admin.ModelAdmin):
#     prepopulated_fields = {"slug": ["name"]}
#     list_display  = [ 'slug', 'name', ]
#     search_fields = ['name']
# 
# admin.site.register( FooBar, FooBarAdmin )
