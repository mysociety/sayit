from django.contrib import admin
from django.db import models

from speeches.models import Speech
from speeches.widgets import AudioFileInput

class SpeechAdmin(admin.ModelAdmin):
    formfield_overrides = {
        models.FileField: { 'widget': AudioFileInput },
    }

admin.site.register(Speech, SpeechAdmin)

# class FooBarAdmin(admin.ModelAdmin):
#     prepopulated_fields = {"slug": ["name"]}
#     list_display  = [ 'slug', 'name', ]
#     search_fields = ['name']
# 
# admin.site.register( FooBar, FooBarAdmin )
