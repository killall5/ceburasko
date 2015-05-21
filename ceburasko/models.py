from django.db.models import *
from version_field import *


class Project(Model):
    name = CharField(max_length=200)

    def __unicode__(self):
        return self.name


class SourcePath(Model):
    project = ForeignKey(Project)
    path_substring = CharField(max_length=255)


class KindPriority(Model):
    project = ForeignKey(Project)
    kind = CharField(max_length=150)
    priority = IntegerField(default=0)


class UnknownKind(Model):
    project = ForeignKey(Project)
    kind = CharField(max_length=150)
    accidents_count = IntegerField(default=0)


class Issue(Model):
    project = ForeignKey(Project)
    title = CharField(max_length=200)
    description = TextField(null=True, blank=True)
    kind = CharField(max_length=150)
    hash = CharField(max_length=150)
    fixed_version = VersionField(null=True)
    first_affected_version = VersionField()
    last_affected_version = VersionField()
    is_fixed = BooleanField(default=False)
    created_time = DateTimeField(auto_now_add=True, blank=True)
    modified_time = DateTimeField(auto_now_add=True, blank=True)
    priority = IntegerField()

    class Meta:
        ordering = ['-priority']

    def __unicode__(self):
        return self.title if self.title else "Issue #%d" % (self.id, )


class Build(Model):
    project = ForeignKey(Project)
    version = VersionField()
    created_time = DateTimeField(auto_now_add=True, blank=True)
    issues = ManyToManyField(Issue, through='Accident')

    def __unicode__(self):
        return '%s' % (self.version, )


class Binary(Model):
    build = ForeignKey(Build)
    hash = CharField(max_length=150)
    filename = CharField(max_length=255)
    issues = ManyToManyField(Issue, through='Accident')

    def __unicode__(self):
        return "%s (%s)" % (self.filename, self.hash)


class Accident(Model):
    issue = ForeignKey(Issue)
    build = ForeignKey(Build)
    binary = ForeignKey(Binary)
    datetime = DateTimeField(auto_now_add=True, blank=True)
    ip = IPAddressField()
    annotation = TextField(null=True, blank=True)
    user_id = CharField(max_length=40, null=True)

    def __unicode__(self):
        return "Accident #%d" % (self.id, )


class Frame(Model):
    accident = ForeignKey(Accident, related_name='stack')
    pos = IntegerField()
    fn = TextField(null=True, blank=True)
    file = TextField(null=True, blank=True)
    line = IntegerField(null=True)

    class Meta:
        ordering = ['pos']

    def __unicode__(self):
        return '#%d %s%s' % (
            self.pos,
            self.function,
            ' at %s:%d' % (self.file, self.line) if self.file and self.line else ''
        )

    @property
    def function(self):
        return self.fn if self.fn else '??'


import urllib2
import yaml


class ForeignTracker(Model):
    JIRA = 'JIRA'
    FOREIGN_TRACKER_CHOICES = (
        (JIRA, 'Atlassian JIRA'),
    )
    title = CharField(max_length=40)
    url = URLField()
    type = CharField(max_length=20, choices=FOREIGN_TRACKER_CHOICES, default=JIRA)
    auth_header = CharField(max_length=200)

    def __unicode__(self):
        return self.title
    
    def get_issue_property(self, issue_id, prop):
        fns = {
            ForeignTracker.JIRA: {
                'url': self.get_jira_issue_url,
                'status': self.get_jira_issue_status,
            }
        }
        try:
            return fns[str(self.type)][prop](issue_id)
        except:
            pass

    def get_jira_issue_url(self, issue_id):
        return '%s/browse/%s' % (self.url, issue_id)

    def request_jira_api(self, url):
        request = urllib2.Request(url)
        request.add_header("Authorization", self.auth_header) 
        return yaml.load(urllib2.urlopen(request, timeout=2).read())

    def get_jira_issue_status(self, issue_id):
        response = self.request_jira_api('%s/rest/api/latest/issue/%s' % (self.url, issue_id))
        return response['fields']['status']['statusCategory']['key'] == 'done', response['fields']['status']['name']


class ForeignIssue(Model):
    key = CharField(max_length=40)
    tracker = ForeignKey(ForeignTracker)
    issue = ForeignKey(Issue)

    @property
    def status(self):
        return self.tracker.get_issue_property(self.key, 'status')

    @property
    def url(self):
        return self.tracker.get_issue_property(self.key, 'url')


class Minidump(Model):
    user_id = CharField(max_length=40)
    ip_address = IPAddressField()
    filepath = CharField(max_length=256)
    modified_time = DateTimeField(auto_now_add=True, blank=True)
