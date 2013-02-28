# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Instance'
        db.create_table('instances_instance', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('label', self.gf('instances.fields.DNSLabelField')(unique=True, max_length=63, db_index=True)),
        ))
        db.send_create_signal('instances', ['Instance'])


    def backwards(self, orm):
        # Deleting model 'Instance'
        db.delete_table('instances_instance')


    models = {
        'instances.instance': {
            'Meta': {'object_name': 'Instance'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'label': ('instances.fields.DNSLabelField', [], {'unique': 'True', 'max_length': '63', 'db_index': 'True'})
        }
    }

    complete_apps = ['instances']