from django.db.models import *
from django.utils import timezone
from django.utils.six import with_metaclass


class Version():
    def __init__(self, value=None):
        if value is None:
            self.raw = tuple()
        elif isinstance(value, tuple) or isinstance(value, list):
            self.raw = tuple(value[:4])
        else:
            self.raw = map(int, value.split('.'))

    def __str__(self):
        return '.'.join(map(str, self.raw))

    def __unicode__(self):
        return self.__str__()

    def __lt__(self, other):
        if not isinstance(other, Version):
            raise NotImplementedError()
        return self.raw < other.raw

    @property
    def major(self):
        return self.raw[0]

    @property
    def minor(self):
        return self.raw[1]

    @property
    def bugfix(self):
        return self.raw[2]

    @property
    def build(self):
        return self.raw[3]


class VersionField(with_metaclass(SubfieldBase, IntegerField)):
    def db_type(self, connection):
        return 'bigint'  # Note this won't work with Oracle.

    def to_python(self, value):
        if isinstance(value, Version):
            return value
        if value is None:
            return None
        value, build  = value/1000000, value%1000000
        value, bugfix = value/10000,   value%10000
        major, minor  = value/10000,   value%10000
        return Version((major, minor, bugfix, build))

    def get_prep_value(self, value):
        if value is None:
            return None
        return value.build + 1000000*(value.bugfix + 10000*(value.minor + 10000*value.major))


class Project(Model):
    name = CharField(max_length=200)

    def __unicode__(self):
        return self.name


class SourcePath(Model):
    project = ForeignKey(Project)
    path_substring = CharField(max_length=255)


class Build(Model):
    project = ForeignKey(Project)
    version = VersionField()
    created_time = DateTimeField(auto_now_add=True, blank=True)

    def __unicode__(self):
        return 'Build %s' % (self.version, )


class Binary(Model):
    build = ForeignKey(Build)
    hash = CharField(max_length=150)
    filename = CharField(max_length=255)


class Issue(Model):
    project = ForeignKey(Project)
    title = CharField(max_length=200)
    description = TextField(null=True, blank=True)
    hash = CharField(max_length=150)
    fixed_version = VersionField(null=True)
    is_fixed = BooleanField(default=False)
    created_time = DateTimeField(auto_now_add=True, blank=True)
    modified_time = DateTimeField()
    priority = IntegerField(default=0)


class AccidentData(Model):
    time = DateTimeField()
    ip = IPAddressField()
    description = TextField(null=True, blank=True)


class Accident(Model):
    issue = ForeignKey(Issue)
    build = ForeignKey(Build)
    binary = ForeignKey(Binary)
    accident_data = OneToOneField(AccidentData)


class Frame(Model):
    accident = ForeignKey(Accident)
    pos = IntegerField()
    fn = TextField(null=True, blank=True)
    file = TextField(null=True, blank=True)
    line = IntegerField(null=True)

    def __unicode__(self):
        return '#%d %s%s' % (
            self.pos,
            self.function,
            ' at %s:%d' % (self.file, self.line) if self.file and self.line else ''
        )

    @property
    def function(self):
        if self.fn:
            return self.fn
        else:
            return '??'


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
    key = CharField(max_length = 40)
    tracker = ForeignKey(ForeignTracker)
    issue = ForeignKey(Issue)

    @property
    def status(self):
        return self.tracker.get_issue_property(self.key, 'status')

    @property
    def url(self):
        return self.tracker.get_issue_property(self.key, 'url')

