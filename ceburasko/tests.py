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
from gdb import parse_gdb
import os.path


class GdbParseTest(TestCase):
    def setUp(self):
        self.basedir = os.path.join(os.path.dirname(gdb.__file__), '')

    def test_assert_parsing(self):
        with open(self.basedir + 'data/01-gdb-abort.txt')) as f:
            errors = parse_gdb(f)
        errors = list(errors)
        self.assertEqual(len(errors), 1)
        error = errors[0]
        self.assertEqual(error['kind'], 'killed')
        self.assertEqual(error['stack'][0]['file'], 'open_catalog.c')
        self.assertEqual(error['stack'][0]['fn'], '__GI___open_catalog')
        self.assertEqual(error['stack'][0]['line'], '49')


class UploadAccidentTest(TestCase):
    def setUp(self):
        self.basedir = os.path.join(os.path.dirname(gdb.__file__), '')
        self.project = Project.objects.create(name='FooBar')
        SourcePath.objects.create(project=self.project, path_substring='/foobar/')
        KindPriority.objects.create(project=self.project, kind='killed', priority=100)
        self.build = Build.objects.create(project=self.project, version=Version('1.0.0.0'))
        Binary.objects.create(build=self.build, hash='fake:asdf', filename='bin/true')
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
        unknown_kind = UnknownKind.objects.get(kind='stopped')
        self.assertEqual(unknown_kind.accidents_count, 1)

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

    def test_speed_test(self):
        with open(self.basedir + 'data/upload-accidents.yaml') as f:
            payload = f.read()

        Binary.objects.create(build=self.build, hash='build-id:6fe4f1971b42bf59a4c2c0151814d2ef40883fa8', filename='bin/bash', )
        KindPriority.objects.create(project=self.project, kind='InvalidRead', priority=10)
        KindPriority.objects.create(project=self.project, kind='InvalidWrite', priority=10)
        SourcePath.objects.create(project=self.project, path_substring="parts/libp2ptv")

        response = self.client.post('/crashes/upload-accidents/', payload, content_type='application/yaml')
        self.assertEqual(response.status_code, 200)
        response = yaml.load(response.content)
        for r in response:
            self.assertEqual(r['action'], 'accepted')
        self.assertNotEqual(response[0]['issue'], response[1]['issue'])
        self.assertNotEqual(response[0]['issue'], response[3]['issue'])
        self.assertNotEqual(response[0]['issue'], response[5]['issue'])

        self.assertEqual(response[1]['issue'], response[2]['issue'])
        self.assertNotEqual(response[1]['issue'], response[3]['issue'])
        self.assertNotEqual(response[1]['issue'], response[5]['issue'])

        self.assertEqual(response[3]['issue'], response[4]['issue'])
        self.assertNotEqual(response[3]['issue'], response[5]['issue'])

        self.assertEqual(response[5]['issue'], response[6]['issue'])
