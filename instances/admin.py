from django.contrib import admin
from django.db import models

from .models import Instance

class InstanceAdmin(admin.ModelAdmin):
    pass

admin.site.register(Instance, InstanceAdmin)

