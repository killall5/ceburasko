# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import ceburasko.version_field


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Accident',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('datetime', models.DateTimeField(auto_now_add=True)),
                ('ip', models.IPAddressField()),
                ('annotation', models.TextField(null=True, blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Binary',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('hash', models.CharField(max_length=150)),
                ('filename', models.CharField(max_length=255)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Build',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('version', ceburasko.version_field.VersionField()),
                ('created_time', models.DateTimeField(auto_now_add=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ForeignIssue',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('key', models.CharField(max_length=40)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ForeignTracker',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=40)),
                ('url', models.URLField()),
                ('type', models.CharField(default=b'JIRA', max_length=20, choices=[(b'JIRA', b'Atlassian JIRA')])),
                ('auth_header', models.CharField(max_length=200)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Frame',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('pos', models.IntegerField()),
                ('fn', models.TextField(null=True, blank=True)),
                ('file', models.TextField(null=True, blank=True)),
                ('line', models.IntegerField(null=True)),
                ('accident', models.ForeignKey(related_name='stack', to='ceburasko.Accident')),
            ],
            options={
                'ordering': ['pos'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Issue',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField(null=True, blank=True)),
                ('kind', models.CharField(max_length=150)),
                ('hash', models.CharField(max_length=150)),
                ('fixed_version', ceburasko.version_field.VersionField(null=True)),
                ('first_affected_version', ceburasko.version_field.VersionField()),
                ('last_affected_version', ceburasko.version_field.VersionField()),
                ('is_fixed', models.BooleanField(default=False)),
                ('created_time', models.DateTimeField(auto_now_add=True)),
                ('modified_time', models.DateTimeField(auto_now_add=True)),
                ('priority', models.IntegerField()),
            ],
            options={
                'ordering': ['-priority'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='KindPriority',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('kind', models.CharField(max_length=150)),
                ('priority', models.IntegerField(default=0)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Project',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=200)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='SourcePath',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('path_substring', models.CharField(max_length=255)),
                ('project', models.ForeignKey(to='ceburasko.Project')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='UnknownKind',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('kind', models.CharField(max_length=150)),
                ('accidents_count', models.IntegerField(default=0)),
                ('project', models.ForeignKey(to='ceburasko.Project')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='kindpriority',
            name='project',
            field=models.ForeignKey(to='ceburasko.Project'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='issue',
            name='project',
            field=models.ForeignKey(to='ceburasko.Project'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='foreignissue',
            name='issue',
            field=models.ForeignKey(to='ceburasko.Issue'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='foreignissue',
            name='tracker',
            field=models.ForeignKey(to='ceburasko.ForeignTracker'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='build',
            name='issues',
            field=models.ManyToManyField(to='ceburasko.Issue', through='ceburasko.Accident'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='build',
            name='project',
            field=models.ForeignKey(to='ceburasko.Project'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='binary',
            name='build',
            field=models.ForeignKey(to='ceburasko.Build'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='binary',
            name='issues',
            field=models.ManyToManyField(to='ceburasko.Issue', through='ceburasko.Accident'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='accident',
            name='binary',
            field=models.ForeignKey(to='ceburasko.Binary'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='accident',
            name='build',
            field=models.ForeignKey(to='ceburasko.Build'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='accident',
            name='issue',
            field=models.ForeignKey(to='ceburasko.Issue'),
            preserve_default=True,
        ),
    ]
