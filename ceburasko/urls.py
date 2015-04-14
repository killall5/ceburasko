from django.conf.urls import patterns, include, url
from django.views.generic import DetailView, ListView
from ceburasko.models import Project

urlpatterns = patterns('ceburasko.views',
    url(r'^$', 'project_list', name='projects'),
    url(r'^project-(?P<project_id>\d+)/$', 'project_details', name='project_details'),

    url(r'^project-(?P<project_id>\d+)/issues/$', 'issue_list', {'is_fixed': False}, name='issues'),
    url(r'^project-(?P<project_id>\d+)/issues/fixed/$', 'issue_list', {'is_fixed': True}, name='fixed-issues'),

    url(r'^project-(?P<project_id>\d+)/builds/$', 'build_list', name='builds'),
    url(r'^build-(?P<build_id>\d+)/$', 'build_details', name='build_details'),

    url(r'^project-(?P<project_id>\d+)/upload-binaries/$', 'upload_binaries'),
    url(r'^upload-accidents/$', 'upload_accidents'),

    url(r'^issue-(?P<issue_id>\d+)/$', 'issue_details', name='issue_details'),
    url(r'^issue-(?P<issue_id>\d+)/modify/$', 'issue_modify', name='issue_modify'),
    url(r'^issue-(?P<issue_id>\d+)/delete/$', 'issue_delete', name='issue_delete'),

    url(r'^accident-(?P<accident_id>\d+)/$', 'accident_details', name='accident_details'),
)
