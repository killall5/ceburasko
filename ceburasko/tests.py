"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase, Client
from models import *
import yaml


class UploadBinaryTest(TestCase):
    def setUp(self):
        Project.objects.create(name='FooBar')
        self.client = Client()

    def test_upload_new_binary(self):
        payload = {
            'version': '1.0.0.0',
            'components': {
                'fake:asdf': ['bin/moo', 'bin/foo', ],
                'fake:asdfasdf': ['bin/foo2', ],
            }
        }
        response = self.client.post('/crashes/project-1/upload-binaries/', yaml.dump(payload), content_type='application/yaml')
        self.assertEqual(response.status_code, 200)
        response = yaml.load(response.content)
        self.assertEqual(response['version'], '1.0.0.0')
        self.assertEqual(response['binaries_count'], 2)

    def test_upload_existing_binary(self):
        payload = {
            'version': '1.0.0.0',
            'components': {
                'fake:asdf': ['bin/moo', ],
            }
        }
        response = self.client.post('/crashes/project-1/upload-binaries/', yaml.dump(payload), content_type='application/yaml')
        self.assertEqual(response.status_code, 200)
        payload = {
            'version': '1.0.0.0',
            'components': {
                'fake:asdf': ['bin/foo', ],
            }
        }
        response = self.client.post('/crashes/project-1/upload-binaries/', yaml.dump(payload), content_type='application/yaml')
        self.assertEqual(response.status_code, 200)
        response = yaml.load(response.content)
        self.assertEqual(response['binaries_count'], 1)


import gdb
from gdb import errors_from_gdb_log
import os.path


class GdbParseTest(TestCase):
    def setUp(self):
        self.basedir = os.path.join(os.path.dirname(gdb.__file__), '')

    def test_assert_parsing(self):
        errors = errors_from_gdb_log(self.basedir + 'data/01-gdb-abort.txt')
        errors = list(errors)
        self.assertEqual(len(errors), 1)
        error = errors[0]
        self.assertEqual(error['kind'], 'killed')
        self.assertEqual(error['binary_id'], 'fake:asdfasdf')
        self.assertEqual(error['stack'][0]['file'], 'open_catalog.c')
        self.assertEqual(error['stack'][0]['fn'], '__GI___open_catalog')
        self.assertEqual(error['stack'][0]['line'], '49')

    def test_unknown_binary_id(self):
        errors = errors_from_gdb_log(self.basedir + 'data/02-000-gdb-unknown-binary-id.txt')
        errors = list(errors)
        self.assertEqual(len(errors), 0)

    def test_unknown_binary_id_2(self):
        errors = errors_from_gdb_log(self.basedir + 'data/02-001-gdb-unknown-binary-id.txt')
        errors = list(errors)
        self.assertEqual(len(errors), 0)


class UploadAccidentTest(TestCase):
    def setUp(self):
        project = Project.objects.create(name='FooBar')
        SourcePath.objects.create(project=project, path_substring='/foobar/')
        KindPriority.objects.create(project=project, kind='killed', priority=100)
        build = Build.objects.create(project=project, version=Version('1.0.0.0'))
        Binary.objects.create(build=build, hash='fake:asdf', filename='bin/true')
        self.client = Client()

    def test_correct_accident(self):
        accidents = [
            {
                'binary_id': 'fake:asdf',
                'accidents': [
                    {
                        'kind': 'killed',
                        'stack': [
                            {
                                'fn': 'main',
                                'file': '/home/jenkins/workspace/foobar/main.cpp',
                            },
                        ]
                    },
                ]
            },
        ]
        response = self.client.post('/crashes/upload-accidents/', yaml.dump(accidents), content_type='application/yaml')
        self.assertEqual(response.status_code, 200)
        responses = yaml.load(response.content)
        self.assertEqual(len(responses), 1)
        response = responses[0]
        self.assertEqual(response['action'], 'accepted')
        self.assertEqual(response['project'], 1)
        issue = Issue.objects.get(pk=response['issue'])
        self.assertEqual(issue.priority, 100)
        self.assertEqual(issue.first_affected_version, Version('1.0.0.0'))

    def test_unknown_binary_id(self):
        accidents = [
            {
                'binary_id': 'fake:asdfasdf',
                'accidents': [
                    {
                        'kind': 'killed',
                        'stack': [
                            {
                                'fn': 'main',
                                'file': '/home/jenkins/workspace/foobar/main.cpp',
                            },
                        ]
                    },
                ]
            },
        ]
        response = self.client.post('/crashes/upload-accidents/', yaml.dump(accidents), content_type='application/yaml')
        self.assertEqual(response.status_code, 200)
        response = yaml.load(response.content)[0]
        self.assertEqual(response['action'], 'ignored')

    def test_unknown_kind(self):
        accidents = [
            {
                'binary_id': 'fake:asdf',
                'accidents': [
                    {
                        'kind': 'stopped',
                        'stack': [
                            {
                                'fn': 'main',
                                'file': '/home/jenkins/workspace/foobar/main.cpp',
                            },
                        ]
                    },
                ]
            },
        ]
        response = self.client.post('/crashes/upload-accidents/', yaml.dump(accidents), content_type='application/yaml')
        self.assertEqual(response.status_code, 200)
        response = yaml.load(response.content)[0]
        self.assertEqual(response['action'], 'ignored')
        self.assertEqual(response['reason'], 'unknown kind')

    def test_unknown_source(self):
        accidents = [
            {
                'binary_id': 'fake:asdf',
                'accidents': [
                    {
                        'kind': 'killed',
                        'stack': [
                            {
                                'fn': 'main',
                                'file': '/home/jenkins/workspace/foobar_defailed/main.cpp',
                            },
                        ]
                    },
                ]
            },
        ]
        response = self.client.post('/crashes/upload-accidents/', yaml.dump(accidents), content_type='application/yaml')
        self.assertEqual(response.status_code, 200)
        response = yaml.load(response.content)[0]
        self.assertEqual(response['action'], 'ignored')
        self.assertEqual(response['reason'], 'unknown source')

    def test_multiple_accidents_same_issue(self):
        accidents = [
            {
                'binary_id': 'fake:asdf',
                'accidents': [
                    {
                        'kind': 'killed',
                        'stack': [
                            {
                                'fn': 'main',
                                'file': '/home/jenkins/workspace/foobar/main.cpp',
                            },
                        ]
                    },
                    {
                        'kind': 'killed',
                        'stack': [
                            {
                                'fn': 'main',
                                'file': '/home/jenkins/workspace/foobar/main.cpp',
                            },
                        ]
                    },
                ]
            },
        ]
        response = self.client.post('/crashes/upload-accidents/', yaml.dump(accidents), content_type='application/yaml')
        self.assertEqual(response.status_code, 200)
        responses = yaml.load(response.content)
        self.assertEqual(len(responses), 2)
        self.assertEqual(responses[0]['action'], 'accepted')
        self.assertEqual(responses[0], responses[1])

    def test_multiple_accidents_different_issues(self):
        accidents = [
            {
                'binary_id': 'fake:asdf',
                'accidents': [
                    {
                        'kind': 'killed',
                        'stack': [
                            {
                                'fn': 'main',
                                'file': '/home/jenkins/workspace/foobar/main.cpp',
                            },
                        ]
                    },
                    {
                        'kind': 'killed',
                        'stack': [
                            {
                                'fn': 'main2',
                                'file': '/home/jenkins/workspace/foobar/main2.cpp',
                            },
                        ]
                    },
                ]
            },
        ]
        response = self.client.post('/crashes/upload-accidents/', yaml.dump(accidents), content_type='application/yaml')
        self.assertEqual(response.status_code, 200)
        responses = yaml.load(response.content)
        self.assertEqual(len(responses), 2)
        self.assertEqual(responses[0]['action'], 'accepted')
        self.assertEqual(responses[0]['project'], responses[1]['project'])
        self.assertNotEqual(responses[0]['issue'], responses[1]['issue'])