# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Section.description'
        db.add_column('speeches_section', 'description',
                      self.gf('django.db.models.fields.TextField')(default='', blank=True),
                      keep_default=False)

        # Adding field 'Section.source_url'
        db.add_column('speeches_section', 'source_url',
                      self.gf('django.db.models.fields.TextField')(default='', blank=True),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'Section.description'
        db.delete_column('speeches_section', 'description')

        # Deleting field 'Section.source_url'
        db.delete_column('speeches_section', 'source_url')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'instances.instance': {
            'Meta': {'object_name': 'Instance'},
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'created_instances'", 'null': 'True', 'to': "orm['auth.User']"}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'label': ('instances.fields.DNSLabelField', [], {'unique': 'True', 'max_length': '63', 'db_index': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'users': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'instances'", 'blank': 'True', 'to': "orm['auth.User']"})
        },
        'popit.apiinstance': {
            'Meta': {'object_name': 'ApiInstance'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'url': ('popit.fields.ApiInstanceURLField', [], {'unique': 'True', 'max_length': '200'})
        },
        'popit.person': {
            'Meta': {'object_name': 'Person'},
            'api_instance': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['popit.ApiInstance']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'popit_id': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True'}),
            'popit_url': ('popit.fields.PopItURLField', [], {'default': "''", 'max_length': '200', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'summary': ('django.db.models.fields.TextField', [], {'blank': 'True'})
        },
        'speeches.recording': {
            'Meta': {'object_name': 'Recording'},
            'audio': ('django.db.models.fields.files.FileField', [], {'max_length': '255'}),
            'audio_duration': ('django.db.models.fields.IntegerField', [], {'default': '0', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'instance': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['instances.Instance']"}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'start_datetime': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'})
        },
        'speeches.recordingtimestamp': {
            'Meta': {'ordering': "('timestamp',)", 'object_name': 'RecordingTimestamp'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'instance': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['instances.Instance']"}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'recording': ('django.db.models.fields.related.ForeignKey', [], {'default': '0', 'related_name': "'timestamps'", 'to': "orm['speeches.Recording']"}),
            'speaker': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['speeches.Speaker']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'speech': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['speeches.Speech']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'})
        },
        'speeches.section': {
            'Meta': {'ordering': "('id',)", 'unique_together': "(('parent', 'slug', 'instance'),)", 'object_name': 'Section'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'instance': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['instances.Instance']"}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'children'", 'null': 'True', 'to': "orm['speeches.Section']"}),
            'slug': ('sluggable.fields.SluggableField', [], {'unique_with': "('parent', 'instance')", 'max_length': '50', 'populate_from': "'title'"}),
            'source_url': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'title': ('django.db.models.fields.TextField', [], {'blank': 'True'})
        },
        'speeches.slug': {
            'Meta': {'object_name': 'Slug'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'redirect': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'})
        },
        'speeches.speaker': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('instance', 'slug'),)", 'object_name': 'Speaker'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'instance': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['instances.Instance']"}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.TextField', [], {'db_index': 'True'}),
            'person': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['popit.Person']", 'null': 'True', 'on_delete': 'models.PROTECT', 'blank': 'True'}),
            'slug': ('sluggable.fields.SluggableField', [], {'unique_with': "('instance',)", 'max_length': '50', 'populate_from': "'name'"})
        },
        'speeches.speech': {
            'Meta': {'ordering': "('start_date', 'start_time', 'id')", 'object_name': 'Speech'},
            'audio': ('django.db.models.fields.files.FileField', [], {'max_length': '255', 'blank': 'True'}),
            'celery_task_id': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'end_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'end_time': ('django.db.models.fields.TimeField', [], {'null': 'True', 'blank': 'True'}),
            'event': ('django.db.models.fields.TextField', [], {'db_index': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'instance': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['instances.Instance']"}),
            'location': ('django.db.models.fields.TextField', [], {'db_index': 'True', 'blank': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'section': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['speeches.Section']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'source_url': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'speaker': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['speeches.Speaker']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'speaker_display': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'start_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'start_time': ('django.db.models.fields.TimeField', [], {'null': 'True', 'blank': 'True'}),
            'tags': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['speeches.Tag']", 'null': 'True', 'blank': 'True'}),
            'text': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'title': ('django.db.models.fields.TextField', [], {'blank': 'True'})
        },
        'speeches.tag': {
            'Meta': {'object_name': 'Tag'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'instance': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['instances.Instance']"}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'})
        }
    }

    complete_apps = ['speeches']