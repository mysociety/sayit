# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion
import speeches.models
import easy_thumbnails.fields
import sluggable.fields


class Migration(migrations.Migration):

    dependencies = [
        ('instances', '__first__'),
        ('popolo', '__first__'),
        ('contenttypes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Recording',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('audio', models.FileField(max_length=255, upload_to='recordings/%Y-%m-%d/')),
                ('start_datetime', models.DateTimeField(help_text='Datetime of first timestamp associated with recording', null=True, blank=True)),
                ('audio_duration', models.IntegerField(help_text='Duration of recording, in seconds', blank=True, default=0)),
                ('instance', models.ForeignKey(to='instances.Instance')),
            ],
            options={
                'abstract': False,
            },
            bases=(speeches.models.AudioMP3Mixin, models.Model),
        ),
        migrations.CreateModel(
            name='RecordingTimestamp',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('timestamp', models.DateTimeField(db_index=True)),
                ('instance', models.ForeignKey(to='instances.Instance')),
                ('recording', models.ForeignKey(related_name='timestamps', to='speeches.Recording', default=0)),
            ],
            options={
                'ordering': ('timestamp',),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Section',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('num', models.TextField(help_text='The number of the section', verbose_name='number', blank=True)),
                ('heading', models.TextField(help_text='The heading of the section', verbose_name='heading', blank=True)),
                ('subheading', models.TextField(help_text='The subheading of the section', verbose_name='subheading', blank=True)),
                ('description', models.TextField(help_text='Longer description, HTML', verbose_name='description', blank=True)),
                ('start_date', models.DateField(help_text='What date did the section start?', null=True, verbose_name='start date', blank=True)),
                ('start_time', models.TimeField(help_text='What time did the section start?', null=True, verbose_name='start time', blank=True)),
                ('number', models.TextField(verbose_name='document number', blank=True)),
                ('legislature', models.TextField(verbose_name='legislature', blank=True)),
                ('session', models.TextField(help_text='Legislative session', verbose_name='session', blank=True)),
                ('slug', sluggable.fields.SluggableField(verbose_name='slug')),
                ('source_url', models.TextField(verbose_name='source URL', blank=True)),
                ('instance', models.ForeignKey(to='instances.Instance')),
                ('parent', models.ForeignKey(related_name='children', to='speeches.Section', null=True, blank=True, verbose_name='parent')),
            ],
            options={
                'ordering': ('id',),
                'verbose_name': 'section',
                'verbose_name_plural': 'sections',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Slug',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('object_id', models.PositiveIntegerField()),
                ('slug', models.CharField(max_length=255, verbose_name='URL', db_index=True)),
                ('redirect', models.BooleanField(default=False, verbose_name='Redirection')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Speaker',
            fields=[
                ('person_ptr', models.OneToOneField(to='popolo.Person', auto_created=True, parent_link=True, serialize=False, primary_key=True)),
                ('slug', sluggable.fields.SluggableField(verbose_name='slug')),
                ('image_cache', easy_thumbnails.fields.ThumbnailerImageField(help_text='If image is set, a local copy will be stored here.', null=True, upload_to=speeches.models.upload_to, verbose_name='image_cache', blank=True)),
                ('instance', models.ForeignKey(to='instances.Instance')),
            ],
            options={
                'ordering': ('name',),
                'verbose_name': 'speaker',
                'verbose_name_plural': 'speakers',
            },
            bases=('popolo.person', models.Model),
        ),
        migrations.CreateModel(
            name='Speech',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('audio', models.FileField(max_length=255, verbose_name='audio', blank=True, upload_to='speeches/%Y-%m-%d/')),
                ('text', models.TextField(help_text='The text of the speech', verbose_name='text', blank=True)),
                ('num', models.TextField(help_text='The number of the speech, if relevant', verbose_name='number', blank=True)),
                ('heading', models.TextField(help_text='The heading of the speech, if relevant', verbose_name='heading', blank=True)),
                ('subheading', models.TextField(help_text='The subheading of the speech, if relevant', verbose_name='subheading', blank=True)),
                ('event', models.TextField(help_text='Was the speech at a particular event?', db_index=True, verbose_name='event', blank=True)),
                ('location', models.TextField(help_text='Where the speech took place', db_index=True, verbose_name='location', blank=True)),
                ('speaker_display', models.CharField(null=True, max_length=256, blank=True)),
                ('type', models.CharField(help_text='What sort of speech is this?', max_length=32, verbose_name='type', choices=[('speech', 'Speech'), ('question', 'Question'), ('answer', 'Answer'), ('scene', 'Scene'), ('narrative', 'Narrative'), ('summary', 'Summary'), ('other', 'Other')])),
                ('start_date', models.DateField(help_text='What date did the speech start?', null=True, verbose_name='start date', blank=True)),
                ('start_time', models.TimeField(help_text='What time did the speech start?', null=True, verbose_name='start time', blank=True)),
                ('end_date', models.DateField(help_text='What date did the speech end?', null=True, verbose_name='end date', blank=True)),
                ('end_time', models.TimeField(help_text='What time did the speech end?', null=True, verbose_name='end time', blank=True)),
                ('public', models.BooleanField(help_text='Is this speech public?', verbose_name='public', default=True)),
                ('source_url', models.TextField(verbose_name='source URL', blank=True)),
                ('celery_task_id', models.CharField(null=True, max_length=256, verbose_name='celery task ID', blank=True)),
                ('instance', models.ForeignKey(to='instances.Instance')),
                ('section', models.ForeignKey(to='speeches.Section', help_text='The section that this speech is contained in', null=True, blank=True, on_delete=django.db.models.deletion.SET_NULL, verbose_name='Section')),
                ('speaker', models.ForeignKey(to='speeches.Speaker', help_text='Who gave this speech?', null=True, blank=True, on_delete=django.db.models.deletion.SET_NULL, verbose_name='speaker')),
            ],
            options={
                'ordering': ('start_date', 'start_time', 'id'),
                'verbose_name': 'speech',
                'verbose_name_plural': 'speeches',
            },
            bases=(speeches.models.AudioMP3Mixin, models.Model),
        ),
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(unique=True, max_length=100)),
                ('instance', models.ForeignKey(to='instances.Instance')),
            ],
            options={
                'verbose_name': 'tag',
                'verbose_name_plural': 'tags',
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='speech',
            name='tags',
            field=models.ManyToManyField(to='speeches.Tag', null=True, verbose_name='tags', blank=True),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='speaker',
            unique_together=set([('instance', 'slug')]),
        ),
        migrations.AlterUniqueTogether(
            name='section',
            unique_together=set([('parent', 'slug', 'instance')]),
        ),
        migrations.AddField(
            model_name='recordingtimestamp',
            name='speaker',
            field=models.ForeignKey(to='speeches.Speaker', null=True, on_delete=django.db.models.deletion.SET_NULL, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='recordingtimestamp',
            name='speech',
            field=models.ForeignKey(to='speeches.Speech', null=True, on_delete=django.db.models.deletion.SET_NULL, blank=True),
            preserve_default=True,
        ),
    ]
