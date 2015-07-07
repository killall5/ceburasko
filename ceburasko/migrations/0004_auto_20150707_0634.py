# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ceburasko', '0003_auto_20150527_0852'),
    ]

    operations = [
        migrations.AddField(
            model_name='accident',
            name='address',
            field=models.CharField(max_length=16, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='accident',
            name='subtype',
            field=models.CharField(max_length=50, null=True),
            preserve_default=True,
        ),
    ]
