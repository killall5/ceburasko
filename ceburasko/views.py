# Create your views here.

from django.shortcuts import get_object_or_404, render_to_response
from ceburasko.models import Project, Issue, CrashReport, Frame, ForeignTracker, ForeignIssue
from django.db.models import Count
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, Http404, HttpResponseRedirect
import yaml
from django.utils import timezone
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

@csrf_exempt
def upload_crash(request, project_id):
    p = get_object_or_404(Project, pk = project_id)
    crash = yaml.load(request.body)
    stack = [Frame(pos=i, **frame) for i, frame in enumerate(crash['stack'])]
    fn_max_length = Frame._meta.get_field('fn').max_length
    for frame in stack:
        if frame.fn:
            frame.fn = frame.fn[:fn_max_length]
    description = '\n'.join([f.function for f in stack])
    stack_hash = Issue.generate_hash(stack)
    try:
        issue = p.issue_set.get(hash = stack_hash)
        issue.modified = timezone.now()
    except:
        issue = Issue.objects.create(hash = stack_hash, project = p, modified = timezone.now(), created = timezone.now(), description = description)
        try:
            issue.title = '#%d %s in %s' % (issue.id, crash['kind'], stack[0].function)
        except:
            issue.title = 'Issue #%d' % issue.id
        issue.title = issue.title[:Issue._meta.get_field('title').max_length]

    cr_params = { 'ip': request.META.get('REMOTE_ADDR') }
    for param in [ 'kind', 'component', 'version', 'annotation' ]:
        if param in crash:
            cr_params[param] = crash[param]
    cr = CrashReport.objects.create(
        issue = issue,
        datetime = timezone.now(),
        **cr_params)
    for frame in stack:
        frame.crashreport_id = cr.id
        frame.save()

    issue.update_last_affected_version(cr.version)
    issue.update_status()
    issue.save()

    return HttpResponse("issue id %s, fixed: %s" % (issue.id, issue.status) )

def get_paginator(source, page_size, page):
    paginator = Paginator(source, page_size)
    try:
        return paginator.page(page)
    except PageNotAnInteger:
        return paginator.page(1)
    except EmptyPage:
        return paginator.page(paginator.num_pages)

def index(request):
    projects = Project.objects.all()
    for p in projects:
        p.opened_issues = p.issue_set.filter(status = False).count()
        p.fixed_issues = p.issue_set.count() - p.opened_issues
    return render_to_response('ceburasko/index.html', { 'projects': projects })

def project_details(request, project_id):
    p = get_object_or_404(Project, pk = project_id)
    opened_issues = get_paginator(
        p.issue_set.annotate(num_crashes = Count('crashreport')).filter(status = False).order_by('-num_crashes'),
        25, request.GET.get('op'))
    fixed_issues = get_paginator(
        p.issue_set.annotate(num_crashes = Count('crashreport')).filter(status = True).order_by('-num_crashes'),
        25, request.GET.get('fp'))
    return render_to_response('ceburasko/project_details.html', {'project': p, 'opened_issues': opened_issues, 'fixed_issues': fixed_issues})
    

from django.template import RequestContext

def issue_details(request, issue_id):
    issue = get_object_or_404(Issue, pk = issue_id)
    # FIXME: needs left join
    foreign_trackers = {}
    for tracker in ForeignTracker.objects.all():
        foreign_trackers[tracker.id] = tracker
    for foreign_issue in issue.foreignissue_set.all():
        foreign_tracker = foreign_trackers[foreign_issue.tracker.id]
        foreign_tracker.issue_key = foreign_issue.key
        foreign_tracker.issue_status = foreign_issue.status
        foreign_tracker.issue_url = foreign_issue.url

    crashes = get_paginator(issue.crashreport_set.order_by('-datetime'), 25, request.GET.get('page'))
    return render_to_response('ceburasko/issue_details.html', 
        { 'issue': issue, 'foreign_trackers': foreign_trackers.values(), 'crashes': crashes, },
        context_instance=RequestContext(request))

def crash_details(request, crash_id):
    crashreport = get_object_or_404(CrashReport, pk = crash_id)
    stack = crashreport.frame_set.order_by('pos').all()
    return render_to_response('ceburasko/crash_details.html', { 'crashreport': crashreport, 'stack': stack })

from django.core.urlresolvers import reverse

def issue_modify(request, issue_id):
    issue = get_object_or_404(Issue, pk = issue_id)
    issue.modified = timezone.now() 
    issue.title = request.POST['title']
    issue.fixed_version = request.POST['fixed_version']
    issue.update_status()
    for tracker in ForeignTracker.objects.all():
        if 'tracker%d' % tracker.id in request.POST:
            if request.POST['tracker%d' % tracker.id]:
                key = request.POST['tracker%d' % tracker.id]
                try:
                    foreign_issue = issue.foreignissue_set.get(tracker = tracker)
                    foreign_issue.key = key
                    foreign_issue.save()
                except:
                    foreign_issue = ForeignIssue.objects.create(tracker = tracker, issue = issue, key = key)
            else:
                try:
                    foreign_issue = issue.foreignissue_set.get(tracker = tracker)
                    foreign_issue.delete()
                except:
                    pass
    issue.save()
    return HttpResponseRedirect(reverse('ceburasko:issue_details', args = (issue.id, )))

def issue_delete(request, issue_id):
    issue = get_object_or_404(Issue, pk = issue_id)
    project_id = issue.project.id
    issue.delete()
    return HttpResponseRedirect(reverse('ceburasko:project_details', args = (project_id, )))
