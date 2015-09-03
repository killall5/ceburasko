# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ceburasko', '0004_auto_20150707_0634'),
    ]

    operations = [
        migrations.AlterField(
            model_name='accident',
            name='ip',
            field=models.GenericIPAddressField(),
        ),
        migrations.AlterField(
            model_name='minidump',
            name='ip_address',
            field=models.GenericIPAddressField(),
        ),
    ]
