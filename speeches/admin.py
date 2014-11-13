from django.contrib import admin
from django.db import models

from speeches.models import Speaker, Speech, Section, Tag
from speeches.widgets import AudioFileInput


class SpeechAdmin(admin.ModelAdmin):
    date_hierarchy = 'start_date'
    list_filter = ('tags',)
    formfield_overrides = {
        models.FileField: {'widget': AudioFileInput},
    }


class SectionAdmin(admin.ModelAdmin):
    search_fields = ('num', 'heading', 'subheading')
    prepopulated_fields = {'slug': ('num', 'heading', 'subheading')}


admin.site.register(Section, SectionAdmin)
admin.site.register(Speaker)
admin.site.register(Speech, SpeechAdmin)
admin.site.register(Tag)

# class FooBarAdmin(admin.ModelAdmin):
#     prepopulated_fields = {"slug": ["name"]}
#     list_display  = [ 'slug', 'name', ]
#     search_fields = ['name']
#
# admin.site.register( FooBar, FooBarAdmin )
