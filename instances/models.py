from django.db import models
from .fields import DNSLabelField

class Instance(models.Model):
    label = DNSLabelField( db_index=True, unique=True )

class InstanceMixin(models.Model):
    instance = models.ForeignKey(Instance)

    class Meta:
        abstract = True

