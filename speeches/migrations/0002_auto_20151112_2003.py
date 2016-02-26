# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('speeches', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='speaker',
            options={'verbose_name': 'speaker', 'verbose_name_plural': 'speakers'},
        ),
        migrations.AlterField(
            model_name='recording',
            name='instance',
            field=models.ForeignKey(verbose_name='instance', to='instances.Instance'),
        ),
        migrations.AlterField(
            model_name='recordingtimestamp',
            name='instance',
            field=models.ForeignKey(verbose_name='instance', to='instances.Instance'),
        ),
        migrations.AlterField(
            model_name='section',
            name='instance',
            field=models.ForeignKey(verbose_name='instance', to='instances.Instance'),
        ),
        migrations.AlterField(
            model_name='speaker',
            name='instance',
            field=models.ForeignKey(verbose_name='instance', to='instances.Instance'),
        ),
        migrations.AlterField(
            model_name='speech',
            name='instance',
            field=models.ForeignKey(verbose_name='instance', to='instances.Instance'),
        ),
        migrations.AlterField(
            model_name='speech',
            name='tags',
            field=models.ManyToManyField(to='speeches.Tag', verbose_name='tags', blank=True),
        ),
        migrations.AlterField(
            model_name='tag',
            name='instance',
            field=models.ForeignKey(verbose_name='instance', to='instances.Instance'),
        ),
    ]
