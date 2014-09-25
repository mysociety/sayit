# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Speech'
        db.create_table('speeches_speech', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('audio', self.gf('django.db.models.fields.files.FileField')(max_length=255, blank=True)),
            ('text', self.gf('django.db.models.fields.TextField')(db_index=True, blank=True)),
            ('title', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('event', self.gf('django.db.models.fields.TextField')(db_index=True, blank=True)),
            ('location', self.gf('django.db.models.fields.TextField')(db_index=True, blank=True)),
            ('speaker', self.gf('django.db.models.fields.TextField')(db_index=True, blank=True)),
            ('start', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('end', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('source_url', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal('speeches', ['Speech'])


    def backwards(self, orm):
        # Deleting model 'Speech'
        db.delete_table('speeches_speech')


    models = {
        'speeches.speech': {
            'Meta': {'object_name': 'Speech'},
            'audio': ('django.db.models.fields.files.FileField', [], {'max_length': '255', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'end': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'event': ('django.db.models.fields.TextField', [], {'db_index': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location': ('django.db.models.fields.TextField', [], {'db_index': 'True', 'blank': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'source_url': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'speaker': ('django.db.models.fields.TextField', [], {'db_index': 'True', 'blank': 'True'}),
            'start': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'text': ('django.db.models.fields.TextField', [], {'db_index': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.TextField', [], {'blank': 'True'})
        }
    }

    complete_apps = ['speeches']