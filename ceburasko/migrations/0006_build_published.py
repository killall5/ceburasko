# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ceburasko', '0005_auto_20150903_1101'),
    ]

    operations = [
        migrations.AddField(
            model_name='build',
            name='published',
            field=models.BooleanField(default=False),
        ),
    ]
