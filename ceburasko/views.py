from django.shortcuts import get_object_or_404, get_list_or_404, render_to_response
from ceburasko.models import *
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, HttpResponseRedirect
import yaml
from django.utils import timezone
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.urlresolvers import reverse
from django.template import RequestContext
from django.db.models import Count
from django.conf import settings
from context_processors import set_default_order, to_order_by
from ceburasko.utils import create_or_update_issue, UnknownSourceError
import hashlib
import os


"""
 Helper for paginate source
"""


def get_paginator(source, page_size, page):
    paginator = Paginator(source, page_size)
    try:
        return paginator.page(page)
    except PageNotAnInteger:
        return paginator.page(1)
    except EmptyPage:
        return paginator.page(paginator.num_pages)


"""
 Ceburasko main page

 Show list of projects
"""


def project_list(request):
    projects = Project.objects.all()
    for p in projects:
        p.opened_issues = p.issue_set.filter(is_fixed=False).count()
        p.fixed_issues = p.issue_set.count() - p.opened_issues
    return render_to_response(
        'ceburasko/project_list.html',
        {'projects': projects},
        context_instance=RequestContext(request)
    )


"""
 Project details page

 Show related issues
"""


def project_details(request, project_id):
    set_default_order('-priority')
    p = get_object_or_404(Project, pk=project_id)
    context = RequestContext(request)
    order_by = to_order_by(context['order'])
    opened_issues = p.issue_set.filter(is_fixed=False).annotate(accidents_count=Count('accident')).order_by(order_by)
    opened_issues_count = len(opened_issues)
    opened_issues = opened_issues[:5]
    fixed_issues = p.issue_set.filter(is_fixed=True).annotate(accidents_count=Count('accident')).order_by(order_by)
    fixed_issues_count = len(fixed_issues)
    fixed_issues = fixed_issues[:5]
    builds = p.build_set.all()[:5]

    return render_to_response(
        'ceburasko/project_details.html',
        {
            'project': p,
            'opened_issues': opened_issues,
            'opened_issues_count': opened_issues_count,
            'fixed_issues': fixed_issues,
            'fixed_issues_count': fixed_issues_count,
            'builds': builds,
        },
        context_instance=context,
    )


"""
 Project issues list
"""


def issue_list(request, project_id, is_fixed=False):
    set_default_order('-priority')
    p = get_object_or_404(Project, pk=project_id)
    context = RequestContext(request)
    order_by = to_order_by(context['order'])
    issues = p.issue_set.filter(is_fixed=is_fixed).annotate(accidents_count=Count('accident')).order_by(order_by)
    issues_paged = get_paginator(issues, 50, request.GET.get('page'))

    return render_to_response(
        'ceburasko/issue_list.html',
        {
            'is_fixed': is_fixed,
            'project': p,
            'issues': issues_paged,
        },
        context_instance=context
    )

"""
 Project builds list
"""


def build_list(request, project_id):
    p = get_object_or_404(Project, pk=project_id)
    builds_paged = get_paginator(p.build_set, 25, request.GET.get('page'))

    return render_to_response(
        'ceburasko/build_list.html',
        {'project': p, 'builds': builds_paged},
        context_instance=RequestContext(request)
    )


"""
 Build details
"""


def build_details(request, build_id):
    build = get_object_or_404(Build, pk=build_id)
    return render_to_response(
        'ceburasko/build_details.html',
        {'build': build},
        context_instance=RequestContext(request)
    )


"""
 Upload new binary info

 If needed, new build in project created
"""


@csrf_exempt
def upload_binaries(request, project_id):
    p = get_object_or_404(Project, pk=project_id)
    payload = yaml.load(request.body)
    version = Version(payload['version'])
    components = payload['components']
    try:
        build = p.build_set.get(version=version)
        action = "updated"
    except ObjectDoesNotExist as e:
        build = Build.objects.create(project=p, version=version, created_time=timezone.now())
        action = "created"
    for binary_id, components in components.items():
        if not components:
            continue
        component = components[0]
        try:
            binary = Binary.objects.get(hash=binary_id)
            binary.build = build
            binary.filename = component
            binary.save()
        except ObjectDoesNotExist as e:
            Binary.objects.create(build=build, hash=binary_id, filename=components[0])
    response = {
        'action': action,
        'version': str(build.version),
        'binaries_count': build.binary_set.count(),
    }
    return HttpResponse(yaml.dump(response))


"""
 Batch upload accidents
"""


@csrf_exempt
def upload_accidents(request):
    payload = yaml.load(request.body)
    if not isinstance(payload, list):
        payload = [payload]
    modified_issues = []
    responses = []
    unknown_kinds = {}
    for case in payload:
        response = {}
        try:
            binary_id = case['binary_id']
        except KeyError as e:
            # No binary_id in accidents? Ignore.
            response['action'] = 'ignored'
            response['reason'] = 'no binary_id key'
            responses.append(response)
            continue
        try:
            affected_binary = Binary.objects.get(hash=binary_id)
            affected_build = affected_binary.build
            project = affected_build.project
        except ObjectDoesNotExist as e:
            # Unknown binary? Ignore.
            response['action'] = 'ignored'
            response['reason'] = 'unknown binary'
            responses.append(response)
            continue
        known_priorities = {}
        for kp in KindPriority.objects.filter(project=project):
            known_priorities[kp.kind] = kp.priority
        for reported_accident in case['accidents']:
            response = {}
            if 'kind' not in reported_accident:
                response['action'] = 'ignored'
                response['reason'] = 'no kind key'
                responses.append(response)
                continue
            try:
                priority_by_accident_kind = known_priorities[reported_accident['kind']]
            except KeyError as e:
                # Ignore accident kinds without priority
                response['action'] = 'ignored'
                response['reason'] = 'unknown kind'
                try:
                    unknown_kinds[reported_accident['kind']] += 1
                except KeyError as e:
                    unknown_kinds[reported_accident['kind']] = 1
                responses.append(response)
                continue
            try:
                issue, accident = create_or_update_issue(
                    affected_binary,
                    reported_accident,
                    request.META.get('REMOTE_ADDR'),
                    priority_by_accident_kind
                )
            except UnknownSourceError as e:
                response['action'] = 'ignored'
                response['reason'] = 'unknown source'
                responses.append(response)
                continue

            response['action'] = 'accepted'
            response['issue'] = issue.id
            response['project'] = issue.project.id
            responses.append(response)

    for kind, count in unknown_kinds.items():
        try:
            unknown_kind = project.unknownkind_set.get(kind=kind)
            unknown_kind.accidents_count += count
            unknown_kind.save()
        except ObjectDoesNotExist as e:
            project.unknownkind_set.create(kind=kind, accidents_count=count)

    # update all modified issues
    modified_time = timezone.now()
    for issue in modified_issues:
        issue.modified_time = modified_time
        # Reopen reproduced issues
        if issue.is_fixed:
            if issue.fixed_version <= issue.last_affected_version:
                issue.is_fixed = False
        issue.save()
    return HttpResponse(yaml.dump(responses))


def issue_details(request, issue_id):
    set_default_order('-datetime')
    issue = get_object_or_404(Issue, pk=issue_id)
    context = RequestContext(request)
    order_by = to_order_by(context['order'])
    # FIXME: needs left join
    foreign_trackers = {}
    for tracker in ForeignTracker.objects.all():
        foreign_trackers[tracker.id] = tracker
    for foreign_issue in issue.foreignissue_set.all():
        foreign_tracker = foreign_trackers[foreign_issue.tracker.id]
        foreign_tracker.issue_key = foreign_issue.key
        foreign_tracker.issue_status = foreign_issue.status
        foreign_tracker.issue_url = foreign_issue.url

    accidents = get_paginator(issue.accident_set.order_by(order_by), 25, request.GET.get('page'))
    return render_to_response(
        'ceburasko/issue_details.html',
        {'issue': issue, 'foreign_trackers': foreign_trackers.values(), 'accidents': accidents, },
        context_instance=context,
    )


def accident_details(request, accident_id):
    accident = get_object_or_404(Accident, pk=accident_id)
    return render_to_response(
        'ceburasko/accident_details.html',
        {'accident': accident},
        context_instance=RequestContext(request)
    )


def issue_modify(request, issue_id):
    issue = get_object_or_404(Issue, pk=issue_id)
    issue.modified = timezone.now()
    issue.title = request.POST['title']
    # issue.description = request.POST['description']
    issue.priority = request.POST['priority']
    if request.POST['fixed_version']:
        issue.fixed_version = Version(request.POST['fixed_version'])
        issue.is_fixed = not issue.fixed_version <= issue.last_affected_version

    else:
        issue.fixed_version = None
        issue.is_fixed = False
    for tracker in ForeignTracker.objects.all():
        if 'tracker%d' % tracker.id in request.POST:
            if request.POST['tracker%d' % tracker.id]:
                key = request.POST['tracker%d' % tracker.id]
                try:
                    foreign_issue = issue.foreignissue_set.get(tracker=tracker)
                    foreign_issue.key = key
                    foreign_issue.save()
                except ObjectDoesNotExist as e:
                    ForeignIssue.objects.create(tracker=tracker, issue=issue, key=key)
            else:
                try:
                    foreign_issue = issue.foreignissue_set.get(tracker=tracker)
                    foreign_issue.delete()
                except ObjectDoesNotExist as e:
                    pass
    issue.modified = timezone.now()
    issue.save()
    return HttpResponseRedirect(reverse('ceburasko:issue_details', args=(issue.id, )))


def issue_delete(request, issue_id):
    issue = get_object_or_404(Issue, pk=issue_id)
    project_id = issue.project.id
    issue.delete()
    return HttpResponseRedirect(reverse('ceburasko:project_details', args=(project_id, )))


def source_list(request, project_id):
    p = get_object_or_404(Project, pk=project_id)
    return render_to_response(
        'ceburasko/source_list.html',
        {'project': p},
        context_instance=RequestContext(request),
    )


def source_add(request, project_id):
    p = get_object_or_404(Project, pk=project_id)
    p.sourcepath_set.create(path_substring=request.POST['path'])
    return HttpResponseRedirect(reverse('ceburasko:sources', args=(p.id, )))


def source_delete(request, project_id, source_id):
    p = get_object_or_404(Project, pk=project_id)
    p.sourcepath_set.get(pk=source_id).delete()
    return HttpResponseRedirect(reverse('ceburasko:sources', args=(p.id, )))


def kind_list(request, project_id):
    p = get_object_or_404(Project, pk=project_id)
    return render_to_response(
        'ceburasko/kind_list.html',
        {'project': p},
    )


def known_kind_list(request, project_id):
    p = get_object_or_404(Project, pk=project_id)
    response = {}
    for kp in KindPriority.objects.filter(project=p).all():
        response[kp.kind] = kp.priority
    return HttpResponse(yaml.dump(response))


@csrf_exempt
def upload_breakpad_symbol(request, project_id):
    p = get_object_or_404(Project, pk=project_id)
    version = Version(request.POST['version'])
    try:
        build = p.build_set.get(version=version)
    except ObjectDoesNotExist as e:
        build = p.build_set.create(version=version)
    debug_identifier = request.POST['debug_identifier']
    debug_filename = request.POST['debug_file']
    binary_id = 'breakpad:%s' % debug_identifier
    try:
        build.binary_set.get(hash=binary_id)
    except ObjectDoesNotExist as e:
        build.binary_set.create(hash=binary_id, filename=debug_filename)
    symbol_dir = os.path.join(
        settings.BREAKPAD_SYMBOLS_PATH,
        debug_filename,
        debug_identifier,
    )
    try:
        os.makedirs(symbol_dir)
    except:
        pass
    symbol_filename = os.path.join(symbol_dir, debug_filename)
    with open(symbol_filename, 'w') as symbol_file:
        for chunk in request.FILES['symbol_file'].chunks():
            symbol_file.write(chunk)
    return HttpResponse(status=200)


@csrf_exempt
def upload_minidump(request):
    try:
        user_id = request.POST['uid']
    except KeyError as e:
        return HttpResponse(status=400)
    ip = request.META.get('REMOTE_ADDR')
    for minidump in request.FILES.values():
        dir = os.path.join(settings.BREAKPAD_MINIDUMPS_PATH,
                           minidump.name[:1],
                           minidump.name[:2])
        try:
            os.makedirs(dir)
        except:
            pass
        minidump_filepath = os.path.join(dir, minidump.name)
        Minidump.objects.create(user_id=user_id, ip_address=ip, filepath=minidump_filepath)
        with open(minidump_filepath, 'w') as f:
            for chunk in minidump.chunks():
                f.write(chunk)
    return HttpResponse(status=200)
