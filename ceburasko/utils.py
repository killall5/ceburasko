import hashlib
from ceburasko.models import *
from django.utils import timezone
import datetime


class UnknownSourceError(RuntimeError):
    pass


class UnknownAccidentKind(RuntimeError):
    pass


def get_significant_frame(stack, sourcepath_set):
    significant_frame = None
    for frame in stack:
        if 'file' not in frame or not frame['file'] or 'fn' not in frame:
            continue
        for source_path in sourcepath_set:
            if source_path.path_substring in frame['file']:
                significant_frame = frame
                break
        if significant_frame:
            break
    if not significant_frame:
        return None, None
    issue_hash = hashlib.md5()
    issue_hash.update(significant_frame['fn'])
    issue_hash = issue_hash.hexdigest()
    return significant_frame, issue_hash


def create_or_update_issue(affected_binary, raw_accident, ip, user_id=None, accident_time=None):
    affected_build = affected_binary.build
    project = affected_build.project
    try:
        kp = project.kindpriority_set.get(kind=raw_accident['kind'])
        priority = kp.priority
    except:
        raise UnknownAccidentKind('Unknown kind: %s' % raw_accident['kind'])
    significant_frame, issue_hash = get_significant_frame(raw_accident['stack'], project.sourcepath_set.all())
    if not significant_frame:
        raise UnknownSourceError()
    issue, created = project.issue_set.get_or_create(hash=issue_hash, kind=raw_accident['kind'], defaults={
        'title': "%s in %s" % (raw_accident['kind'], significant_frame['fn']),
        'priority': priority,
        'first_affected_version': affected_build.version,
        'last_affected_version': affected_build.version,
    })
    if not created:
        issue.last_affected_version = max(issue.last_affected_version, affected_build.version)
        issue.save()
    if issue.is_fixed and affected_build.version < issue.fixed_version:
        accident = None
    else:
        accident = Accident(
            issue=issue,
            build=affected_build,
            binary=affected_binary,
            ip=ip,
            user_id=user_id,
            datetime=accident_time,
        )
        if 'subtype' in raw_accident:
            accident.subtype = raw_accident['subtype'][:50]
        if 'address' in raw_accident:
            accident.address = raw_accident['address']
        if 'annotation' in raw_accident:
            accident.annotation = raw_accident['annotation']
        accident.save()
        frames = [Frame(accident=accident, pos=i, **frame) for i, frame in enumerate(raw_accident['stack'])]
        Frame.objects.bulk_create(frames)
    return issue, accident


def update_modified_issues(modified_issues):
    modified_time = timezone.now()
    for issue in modified_issues:
        issue.modified_time = modified_time
        # Reopen reproduced issues
        if issue.is_fixed:
            if issue.fixed_version <= issue.last_affected_version:
                issue.is_fixed = False
        issue.save()


"""
 :returns list of day, crashes count
"""
def accidents_by_date_chart(accident_set, last=30):
    today = datetime.date.today()
    chart = {d: 0 for d in [today - datetime.timedelta(i) for i in range(last)]}
    affected_days = accident_set.filter(datetime__gte=today-datetime.timedelta(last)).extra(select={
        'day': 'date(datetime)'
    }).values('day').annotate(count=Count('datetime'))
    for d in affected_days:
        date = d['day']
        # some magic here: sqlite return unicode, postgresql -- datetime.date
        if type(date) != datetime.date:
            date = datetime.date(*map(int, date.split('-')))
        chart[date] = d['count']
    return sorted(chart.iteritems())
