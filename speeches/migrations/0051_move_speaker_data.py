# -*- coding: utf-8 -*-
from south.v2 import DataMigration
from django.utils.encoding import smart_text

# Note: Don't use "from appname.models import ModelName".
# Use orm.ModelName to refer to models in this application,
# and orm['appname.ModelName'] for models in other applications.

import functools
import types

# From http://south.aeracode.org/ticket/325
def get_content_type(orm, app_label, model_name):
    # sometimes these content types are not yet created when this migration runs,
    # so create them here.  mimic behavior of ContentType.objects.get_for_model
    # (which is not available in migrations)
    opts = orm['%s.%s' % (app_label, model_name)]._meta.concrete_model._meta
    ct, created = orm['contenttypes.ContentType'].objects.get_or_create(app_label=app_label,
        model=model_name, defaults={'name': smart_text(opts.verbose_name_raw)})
    return ct

# This function from django-sluggable is needed because the post-delete signal
# on SluggableField (to delete all the attached slugs) calls it
def filter_by_obj(self, obj, **kwargs):
    content_type = kwargs.pop('content_type')
    return self._filter_or_exclude(False, content_type_id=content_type.pk, object_id=obj.pk, **kwargs)

def attach_filter_by_obj(obj, **kwargs):
    obj.filter_by_obj = types.MethodType(functools.partial(filter_by_obj, **kwargs), obj)

class Migration(DataMigration):
    no_dry_run = True

    def forwards(self, orm):
        old_ct = get_content_type(orm, 'speeches', 'speaker')
        new_ct = get_content_type(orm, 'speeches', 'popolospeaker')
        popolo_ct = get_content_type(orm, 'popolo', 'person')

        try:
            an_ai = orm['popit.ApiInstance'].objects.get(url='http://import.example.org/')
        except orm['popit.ApiInstance'].DoesNotExist:
            an_ai = None

        for speaker in orm.Speaker.objects.all():
            # Create new speaker
            new_speaker = orm.PopoloSpeaker(
                name=speaker.name,
                slug=speaker.slug,
                instance=speaker.instance,
            )
            new_speaker.slug_changed = False
            if speaker.person:
                if not new_speaker.name:
                    new_speaker.name = speaker.person.name
                new_speaker.image = speaker.person.image
                new_speaker.summary = speaker.person.summary
            new_speaker.save()

            # Transfer slugs across
            speaker.slugs = orm.Slug.objects.filter(content_type=old_ct, object_id=speaker.id)
            attach_filter_by_obj(speaker.slugs, content_type=old_ct)
            for slug in speaker.slugs:
                slug.content_type = new_ct
                slug.object_id = new_speaker.id
                slug.save()

            # Make sure IDs are transferred appropriately
            if speaker.person:
                if speaker.person.popit_id:
                    scheme = 'PopIt ID'
                    if speaker.person.api_instance == an_ai:
                        scheme = 'Akoma Ntoso import'
                    orm['popolo.Identifier'].objects.create(
                        content_type=popolo_ct,
                        object_id=new_speaker.id,
                        identifier=speaker.person.popit_id,
                        scheme=scheme,
                    )
                if speaker.person.popit_url:
                    orm['popolo.Identifier'].objects.create(
                        content_type=popolo_ct,
                        object_id=new_speaker.id,
                        identifier=speaker.person.popit_url,
                        scheme='PopIt URL',
                    )

            for model in (orm.Speech, orm.RecordingTimestamp):
                model.objects.filter(speaker=speaker).update(speaker_new=new_speaker)

            # Remove the old speaker
            speaker.delete()

        # No speaker objects any more, so no need for any Person objects
        orm['popit.Person'].objects.all().delete()

    def backwards(self, orm):
        old_ct = get_content_type(orm, 'speeches', 'speaker')
        new_ct = get_content_type(orm, 'speeches', 'popolospeaker')
        popolo_ct = get_content_type(orm, 'popolo', 'person')

        an_ai, _ = orm['popit.ApiInstance'].objects.get_or_create(url='http://import.example.org/')
        all_ai, _ = orm['popit.ApiInstance'].objects.get_or_create(url='http://all.example.org/')

        for speaker in orm.PopoloSpeaker.objects.all():
            old_speaker = orm.Speaker(
                name=speaker.name,
                slug=speaker.slug,
                instance=speaker.instance,
            )
            old_speaker.slug_changed = False
            old_speaker.save()

            speaker.slugs = orm.Slug.objects.filter(content_type=new_ct, object_id=speaker.id)
            attach_filter_by_obj(speaker.slugs, content_type=new_ct)
            for slug in speaker.slugs:
                slug.content_type = old_ct
                slug.object_id = old_speaker.id
                slug.save()

            speaker.identifiers = orm['popolo.Identifier'].objects.filter(content_type=popolo_ct, object_id=speaker.id)
            an_imported = speaker.identifiers.filter(scheme='Akoma Ntoso import')
            popit_url = speaker.identifiers.filter(scheme='PopIt URL')
            popit_id = speaker.identifiers.filter(scheme='PopIt ID')

            data = {
                'api_instance': all_ai,
                'name': speaker.name,
                'image': speaker.image or '',
                'summary': speaker.summary,
            }
            if an_imported or speaker.image or speaker.summary or popit_url or popit_id:
                if an_imported:
                    data['api_instance'] = an_ai
                    data['popit_id'] = an_imported[0].identifier
                else:
                    if popit_url:
                        data['popit_url'] = popit_url[0].identifier
                    if popit_id:
                        data['popit_id'] = popit_id[0].identifier
                p = orm['popit.Person'].objects.create(**data)
                old_speaker.person = p
                old_speaker.save()

            for model in (orm.Speech, orm.RecordingTimestamp):
                model.objects.filter(speaker_new=speaker).update(speaker=old_speaker)

            speaker.delete()

        assert orm.PopoloSpeaker.objects.count() == 0, "PopoloSpeaker objects still exist"

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
        'popolo.contactdetail': {
            'Meta': {'object_name': 'ContactDetail'},
            'contact_type': ('django.db.models.fields.CharField', [], {'max_length': '12'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'created_at': ('model_utils.fields.AutoCreatedField', [], {'default': 'datetime.datetime.now'}),
            'end_date': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'label': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            'note': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'start_date': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'}),
            'updated_at': ('model_utils.fields.AutoLastModifiedField', [], {'default': 'datetime.datetime.now'}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '128'})
        },
        'popolo.identifier': {
            'Meta': {'object_name': 'Identifier'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'identifier': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'scheme': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'})
        },
        'popolo.link': {
            'Meta': {'object_name': 'Link'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'note': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200'})
        },
        'popolo.othername': {
            'Meta': {'object_name': 'OtherName'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'end_date': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'note': ('django.db.models.fields.CharField', [], {'max_length': '256', 'blank': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'start_date': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'})
        },
        'popolo.person': {
            'Meta': {'object_name': 'Person'},
            'additional_name': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            'biography': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'birth_date': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'}),
            'created_at': ('model_utils.fields.AutoCreatedField', [], {'default': 'datetime.datetime.now'}),
            'death_date': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'null': 'True', 'blank': 'True'}),
            'end_date': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'}),
            'family_name': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            'gender': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            'given_name': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            'honorific_prefix': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            'honorific_suffix': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'patronymic_name': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            'sort_name': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            'start_date': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'}),
            'summary': ('django.db.models.fields.CharField', [], {'max_length': '512', 'blank': 'True'}),
            'updated_at': ('model_utils.fields.AutoLastModifiedField', [], {'default': 'datetime.datetime.now'})
        },
        'popolo.source': {
            'Meta': {'object_name': 'Source'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'note': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200'})
        },
        'speeches.popolospeaker': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('instance', 'slug'),)", 'object_name': 'PopoloSpeaker', '_ormbases': ['popolo.Person']},
            'instance': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['instances.Instance']"}),
            'person_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['popolo.Person']", 'unique': 'True', 'primary_key': 'True'}),
            'slug': ('sluggable.fields.SluggableField', [], {'unique_with': "('instance',)", 'max_length': '50', 'populate_from': "'name'"})
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
            'speaker_new': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['speeches.PopoloSpeaker']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
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
            'speaker_new': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['speeches.PopoloSpeaker']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
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
    symmetrical = True
