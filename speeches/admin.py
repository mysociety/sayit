from django.contrib import admin
from speeches import models

class SpeechAdmin(admin.ModelAdmin):
    pass

admin.site.register(models.Speech, SpeechAdmin)

# class FooBarAdmin(admin.ModelAdmin):
#     prepopulated_fields = {"slug": ["name"]}
#     list_display  = [ 'slug', 'name', ]
#     search_fields = ['name']
# 
# admin.site.register( models.FooBar, FooBarAdmin )
