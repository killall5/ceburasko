# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ceburasko', '0002_auto_20150521_0550'),
    ]

    operations = [
        migrations.CreateModel(
            name='ApplicationLog',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100)),
                ('content', models.TextField()),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='accident',
            name='logs',
            field=models.ManyToManyField(to='ceburasko.ApplicationLog'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='issue',
            name='save_logs',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
    ]
