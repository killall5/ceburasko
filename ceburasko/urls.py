from django.conf.urls import patterns, include, url
from django.views.generic import DetailView, ListView
from ceburasko.models import Project

urlpatterns = patterns('ceburasko.views',
    url(r'^$', 'index', name = 'index'),
    url(r'^project-(?P<project_id>\d+)/$', 'project_details', name = 'project_details'),

    url(r'^issue-(?P<issue_id>\d+)/$', 'issue_details', name = 'issue_details'),
    url(r'^issue-(?P<issue_id>\d+)/modify/$', 'issue_modify', name = 'issue_modify'),
    url(r'^issue-(?P<issue_id>\d+)/delete/$', 'issue_delete', name = 'issue_delete'),

    url(r'^crash-(?P<crash_id>\d+)/$', 'crash_details', name = 'crash_details'),

    url(r'^project-(?P<project_id>\d+)/upload-crash/$', 'upload_crash'),
)
