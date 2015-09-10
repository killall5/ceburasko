from django.conf.urls import patterns, include, url
from django.views.generic import DetailView, ListView
from ceburasko.models import Project

urlpatterns = patterns('ceburasko.views',
    url(r'^$', 'project_list', name='projects'),
    url(r'^project-(?P<project_id>\d+)/$', 'project_details', name='project_details'),

    url(r'^project-(?P<project_id>\d+)/builds/$', 'build_list', name='builds'),
    url(r'^project-(?P<project_id>\d+)/issues/$', 'issue_list', {'is_fixed': False}, name='issues'),
    url(r'^project-(?P<project_id>\d+)/issues/fixed/$', 'issue_list', {'is_fixed': True}, name='fixed-issues'),

    url(r'^project-(?P<project_id>\d+)/upload-binaries/$', 'upload_binaries'),
    url(r'^project-(?P<project_id>\d+)/upload-symbol/$', 'upload_breakpad_symbol'),

    url(r'^upload-accidents/$', 'upload_accidents'),
    url(r'^upload-minidump/$', 'upload_minidump'),

    url(r'^issue-(?P<issue_id>\d+)/$', 'issue_details', name='issue_details'),
    url(r'^issue-(?P<issue_id>\d+)/modify/$', 'issue_modify', name='issue_modify'),
    url(r'^issue-(?P<issue_id>\d+)/delete/$', 'issue_delete', name='issue_delete'),

    url(r'^accident-(?P<accident_id>\d+)/$', 'accident_details', name='accident_details'),
    url(r'^application-log-(?P<application_log_id>\d+)/$', 'application_log', name='application_log'),

    url(r'^project-(?P<project_id>\d+)/sources/$', 'source_list', name='sources'),
    url(r'^project-(?P<project_id>\d+)/source-add/$', 'source_add', name='source_add'),
    url(r'^project-(?P<project_id>\d+)/source-delete/(?P<source_id>\d+)/$', 'source_delete', name='source_delete'),

    url(r'^project-(?P<project_id>\d+)/kinds/$', 'kind_list', name='kinds'),
    url(r'^project-(?P<project_id>\d+)/known-kinds/$', 'known_kind_list'),

    url(r'^build-(?P<build_id>\d+)/$', 'build_details', name='build_details'),
    url(r'^build-(?P<build_id>\d+)/toggle-published/$', 'build_toggle_published', name='build_toggle_published'),
    url(r'^build-(?P<build_id>\d+)/delete/$', 'build_delete', name='build_delete'),
)
