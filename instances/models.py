from django.db import models
from django.conf import settings

from .fields import DNSLabelField

class Instance(models.Model):
    label = DNSLabelField( db_index=True, unique=True )

    def __unicode__(self):
        return u'Instance %s' % self.label

    def get_absolute_url(self):
        url = 'http://%s.%s' % (self.label, settings.BASE_HOST)
        if settings.BASE_PORT:
            url += ':' + settings.BASE_PORT
        return url

class InstanceMixin(models.Model):
    instance = models.ForeignKey(Instance)

    class Meta:
        abstract = True

