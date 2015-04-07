from django.db import models
from django.utils import timezone
from django.utils.six import with_metaclass

#class Version():
    

class VersionField(with_metaclass(models.SubfieldBase, models.IntegerField)):
    empty_strings_allowed=False
    def get_internal_type(self):
        return "VersionField"	
    def db_type(self):
        return 'bigint' # Note this won't work with Oracle.
    def to_python(self, value):
        if isinstance(value, tuple):
            return value
        value, build  = value/100000, value%100000
        value, bugfix = value/1000,   value%1000
        major, minor  = value/1000,   value%1000
        return (major, minor, bugfix, build)
    def get_prep_value(self, value):
       pass 

def version_from_string(string):
    try:
        return map(int, string.split('.'))
    except:
        return []

def version_to_string(version):
    return '.'.join(map(str, version))

class Project(models.Model):
    name = models.CharField(max_length = 200)

    def __unicode__(self):
        return self.name

class Issue(models.Model):
    project = models.ForeignKey(Project)
    title = models.CharField(max_length = 4000, null = True, blank = True)
    description = models.TextField(null = True, blank = True)
    hash = models.CharField(max_length = 40)
    status = models.BooleanField( default = False )
    last_affected_version = models.CharField(max_length = 40, null = True, blank = True)
    fixed_version = models.CharField(max_length = 40, null = True, blank = True)
    created = models.DateTimeField()
    modified = models.DateTimeField()

    @staticmethod
    def generate_hash(stack):
        from hashlib import sha1
        id = sha1()
        for frame in stack:
            id.update(frame.function)
        return id.hexdigest()
    
    def __unicode__(self):
        return self.title if self.title else 'Issue #%d' % self.id
    
    def update_last_affected_version(self, version):
        try:
            version = version_from_string(version)
            last_affected_version = version_from_string(self.last_affected_version)
            self.last_affected_version = version_to_string(max(version, last_affected_version))
        except:
            pass

    def update_status(self):
        self.status = version_from_string(self.last_affected_version) < version_from_string(self.fixed_version)

class CrashReport(models.Model):
    issue = models.ForeignKey(Issue)
    kind = models.CharField(max_length = 200, null = True, blank = True)
    datetime = models.DateTimeField()
    annotation = models.TextField(null = True, blank = True)
    component = models.CharField(max_length = 40, null = True, blank = True)
    version = models.CharField(max_length = 40, null = True, blank = True)
    ip = models.IPAddressField()

    def __unicode__(self):
        return 'Crash #%d' % self.id

class Frame(models.Model):
    crashreport = models.ForeignKey(CrashReport)
    pos = models.IntegerField()
    fn = models.CharField(max_length = 2000, null = True, blank = True)
    file = models.CharField(max_length = 2000, null = True, blank = True)
    line = models.IntegerField(null = True)

    def __unicode__(self):
        return '#%d %s%s' % (self.pos, self.function, ' at %s:%d' % (self.file, self.line) if self.file and self.line else '')

    @property
    def function(self):
        if self.fn:
            return self.fn
        else:
            return '??'

import urllib2
import yaml

class ForeignTracker(models.Model):
    JIRA = 'JIRA'
    FOREIGN_TRACKER_CHOICES = (
        ( JIRA, 'Atlassian JIRA' ),
    )
    title = models.CharField(max_length = 40)
    url = models.URLField()
    type = models.CharField(max_length = 20, choices = FOREIGN_TRACKER_CHOICES, default = JIRA)
    auth_header = models.CharField(max_length = 200)

    def __unicode__(self):
        return self.title
    
    def get_issue_property(self, issue_id, prop):
        fns = {
            ForeignTracker.JIRA: {
                'url': self.get_JIRA_issue_url,
                'status': self.get_JIRA_issue_status,
            }
        }
        try:
            return fns[self.type][prop](issue_id)
        except Exception as e:
            pass

    def get_JIRA_issue_url(self, issue_id):
        return '%s/browse/%s' % (self.url, issue_id)

    def request_JIRA_API(self, url):
        request = urllib2.Request(url)
        request.add_header("Authorization", self.auth_header) 
        return yaml.load(urllib2.urlopen(request, timeout = 2).read())

    def get_JIRA_issue_status(self, issue_id):
        response = self.request_JIRA_API('%s/rest/api/latest/issue/%s' % (self.url, issue_id))
        return (response['fields']['status']['statusCategory']['key'] == 'done', response['fields']['status']['name'])

class ForeignIssue(models.Model):
    key = models.CharField(max_length = 40)
    tracker = models.ForeignKey(ForeignTracker)
    issue = models.ForeignKey(Issue)

    @property
    def status(self):
        return self.tracker.get_issue_property(self.key, 'status')

    @property
    def url(self):
        return self.tracker.get_issue_property(self.key, 'url')

