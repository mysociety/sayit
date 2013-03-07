from django.db import models
from django.conf import settings
from django.contrib.auth.models import User

from .fields import DNSLabelField

class InstanceManager(models.Manager):
    def for_instance(self, instance):
        return self.get_query_set().filter(instance=instance)

class Instance(models.Model):
    label = DNSLabelField( db_index=True, unique=True )
    title = models.CharField( max_length=100 )
    description = models.TextField( blank=True )
    users = models.ManyToManyField(User, related_name='instances', blank=True)
    created_by = models.ForeignKey(User, related_name='created_instances', null=True, blank=True)

    def __unicode__(self):
        return u'Instance %s' % self.label

    def get_absolute_url(self):
        url = 'http://%s.%s' % (self.label, settings.BASE_HOST)
        if settings.BASE_PORT:
            url += ':' + settings.BASE_PORT
        return url

class InstanceMixin(models.Model):
    instance = models.ForeignKey(Instance)

    objects = InstanceManager()

    class Meta:
        abstract = True

