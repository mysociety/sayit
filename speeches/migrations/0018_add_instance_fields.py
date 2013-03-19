# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    depends_on = (
        ("instances", "0001_initial"),
    )
    needed_by = (
        ("instances", "0002_auto__add_field_instance_description"),
    )

    def forwards(self, orm):
        instance = orm['instances.Instance'](label='default')
        instance.save()

        # Adding field 'Meeting.instance'
        db.add_column('speeches_meeting', 'instance',
                      self.gf('django.db.models.fields.related.ForeignKey')(default=instance.id, to=orm['instances.Instance']),
                      keep_default=False)

        # Adding field 'Debate.instance'
        db.add_column('speeches_debate', 'instance',
                      self.gf('django.db.models.fields.related.ForeignKey')(default=instance.id, to=orm['instances.Instance']),
                      keep_default=False)

        # Adding field 'RecordingTimestamp.instance'
        db.add_column('speeches_recordingtimestamp', 'instance',
                      self.gf('django.db.models.fields.related.ForeignKey')(default=instance.id, to=orm['instances.Instance']),
                      keep_default=False)

        # Adding field 'Speech.instance'
        db.add_column('speeches_speech', 'instance',
                      self.gf('django.db.models.fields.related.ForeignKey')(default=instance.id, to=orm['instances.Instance']),
                      keep_default=False)

        # Adding field 'Speaker.instance'
        db.add_column('speeches_speaker', 'instance',
                      self.gf('django.db.models.fields.related.ForeignKey')(default=instance.id, to=orm['instances.Instance']),
                      keep_default=False)

        # Adding field 'Recording.instance'
        db.add_column('speeches_recording', 'instance',
                      self.gf('django.db.models.fields.related.ForeignKey')(default=instance.id, to=orm['instances.Instance']),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'Meeting.instance'
        db.delete_column('speeches_meeting', 'instance_id')

        # Deleting field 'Debate.instance'
        db.delete_column('speeches_debate', 'instance_id')

        # Deleting field 'RecordingTimestamp.instance'
        db.delete_column('speeches_recordingtimestamp', 'instance_id')

        # Deleting field 'Speech.instance'
        db.delete_column('speeches_speech', 'instance_id')

        # Deleting field 'Speaker.instance'
        db.delete_column('speeches_speaker', 'instance_id')

        # Deleting field 'Recording.instance'
        db.delete_column('speeches_recording', 'instance_id')

        orm['instances.Instance'].objects.get(label='default').delete()

    models = {
        'instances.instance': {
            'Meta': {'object_name': 'Instance'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'label': ('instances.fields.DNSLabelField', [], {'unique': 'True', 'max_length': '63', 'db_index': 'True'})
        },
        'speeches.debate': {
            'Meta': {'object_name': 'Debate'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'instance': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['instances.Instance']"}),
            'meeting': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['speeches.Meeting']", 'null': 'True', 'blank': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'speeches.meeting': {
            'Meta': {'object_name': 'Meeting'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'instance': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['instances.Instance']"}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'speeches.recording': {
            'Meta': {'object_name': 'Recording'},
            'audio': ('django.db.models.fields.files.FileField', [], {'max_length': '255'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'instance': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['instances.Instance']"}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'timestamps': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': "orm['speeches.RecordingTimestamp']", 'null': 'True', 'blank': 'True'})
        },
        'speeches.recordingtimestamp': {
            'Meta': {'object_name': 'RecordingTimestamp'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'instance': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['instances.Instance']"}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'speaker': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['speeches.Speaker']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'})
        },
        'speeches.speaker': {
            'Meta': {'object_name': 'Speaker'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'instance': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['instances.Instance']"}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.TextField', [], {'db_index': 'True'}),
            'popit_url': ('django.db.models.fields.TextField', [], {'unique': 'True'})
        },
        'speeches.speech': {
            'Meta': {'object_name': 'Speech'},
            'audio': ('django.db.models.fields.files.FileField', [], {'max_length': '255', 'blank': 'True'}),
            'celery_task_id': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'debate': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['speeches.Debate']", 'null': 'True', 'blank': 'True'}),
            'end_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'end_time': ('django.db.models.fields.TimeField', [], {'null': 'True', 'blank': 'True'}),
            'event': ('django.db.models.fields.TextField', [], {'db_index': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'instance': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['instances.Instance']"}),
            'location': ('django.db.models.fields.TextField', [], {'db_index': 'True', 'blank': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'source_url': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'speaker': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['speeches.Speaker']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'start_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'start_time': ('django.db.models.fields.TimeField', [], {'null': 'True', 'blank': 'True'}),
            'text': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'title': ('django.db.models.fields.TextField', [], {'blank': 'True'})
        }
    }

    complete_apps = ['speeches']
