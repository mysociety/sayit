# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Instance.title'
        db.add_column('instances_instance', 'title',
                      self.gf('django.db.models.fields.CharField')(default='An instance', max_length=100),
                      keep_default=False)

        # Adding field 'Instance.description'
        db.add_column('instances_instance', 'description',
                      self.gf('django.db.models.fields.TextField')(default='', blank=True),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'Instance.title'
        db.delete_column('instances_instance', 'title')

        # Deleting field 'Instance.description'
        db.delete_column('instances_instance', 'description')


    models = {
        'instances.instance': {
            'Meta': {'object_name': 'Instance'},
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'label': ('instances.fields.DNSLabelField', [], {'unique': 'True', 'max_length': '63', 'db_index': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['instances']