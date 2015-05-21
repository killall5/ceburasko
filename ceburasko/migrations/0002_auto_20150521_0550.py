# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ceburasko', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Minidump',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('user_id', models.CharField(max_length=40)),
                ('ip_address', models.IPAddressField()),
                ('filepath', models.CharField(max_length=256)),
                ('modified_time', models.DateTimeField(auto_now_add=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='accident',
            name='user_id',
            field=models.CharField(max_length=40, null=True),
            preserve_default=True,
        ),
    ]
