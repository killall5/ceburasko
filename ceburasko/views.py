from django.shortcuts import get_object_or_404, render_to_response
from ceburasko.models import *
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.urlresolvers import reverse
from django.template import RequestContext
from context_processors import set_default_order, to_order_by
from ceburasko.utils import *
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
    projects = Project.objects.all().extra(select={
        'opened_issues': "select count(*) from ceburasko_issue where "
                         "ceburasko_issue.project_id = ceburasko_project.id and "
                         "not ceburasko_issue.is_fixed",
        'fixed_issues': "select count(*) from ceburasko_issue where "
                         "ceburasko_issue.project_id = ceburasko_project.id and "
                         "ceburasko_issue.is_fixed",
    })
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
    opened_issues = p.issue_set.filter(is_fixed=False)
    fixed_issues = p.issue_set.filter(is_fixed=True)

    return render_to_response(
        'ceburasko/project_details.html',
        {
            'project': p,
            'opened_issues': opened_issues,
            'fixed_issues': fixed_issues,
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
    issues = p.issue_set.extra(select={
       'users_affected': "select count(distinct user_id) from ceburasko_accident "
                         "where ceburasko_accident.issue_id = ceburasko_issue.id",
       'accidents_count': "select count(*) from ceburasko_accident "
                          "where ceburasko_accident.issue_id = ceburasko_issue.id",
    }).filter(is_fixed=is_fixed).order_by(order_by)
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
    build, created = p.build_set.get_or_create(version=version)
    action = "created" if created else "updated"
    for binary_id, components in components.items():
        if not components:
            continue
        component = components[0]
        binary = build.binary_set.update_or_create(hash=binary_id, defaults={
            'filename': component
        })
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
    modified_issues = {}
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
        logs = {}
        if 'logs' in case:
            for name, content in case['logs'].items():
                logs[name] = {
                    'name': name,
                    'content': content,
                    'model': None,
                }
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
                    request.META.get('REMOTE_ADDR')
                )
            except UnknownSourceError as e:
                response['action'] = 'ignored'
                response['reason'] = 'unknown source'
                responses.append(response)
                continue

            if accident is None:
                response['action'] = 'ignored'
                response['issue'] = issue.id
                response['reason'] = 'already fixed in %s' % (issue.fixed_version, )
                responses.append(response)
                continue

            modified_issues[issue.id] = issue
            if issue.save_logs and 'logs' in reported_accident:
                for log in reported_accident['logs']:
                    if log in logs:
                        log = logs[log]
                        if log['model'] is None:
                            log['model'] = ApplicationLog.objects.create(name=log['name'], content=log['content'])
                            del log['content']
                        accident.logs.add(log['model'])
                accident.save()

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
    update_modified_issues(modified_issues.values())
    return HttpResponse(yaml.dump(responses))


def issue_details(request, issue_id):
    set_default_order('-datetime')
    try:
        issue = Issue.objects.select_related('project').extra(select={
            "users_affected": "select count(distinct user_id) from ceburasko_accident "
                              "where ceburasko_accident.issue_id = ceburasko_issue.id"
        }).get(pk=issue_id)
    except:
        raise Http404("No such issue")
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

    accidents = issue.accident_set.select_related('build', 'binary').extra(select={
        'logs_available': 'select count(*) from ceburasko_accident_logs where '
                          'ceburasko_accident_logs.accident_id = ceburasko_accident.id'
    }).order_by(order_by)
    accidents = get_paginator(accidents, 25, request.GET.get('page'))
    return render_to_response(
        'ceburasko/issue_details.html',
        {'issue': issue,
         'foreign_trackers': foreign_trackers.values(),
         'accidents': accidents,
         },
        context_instance=context,
    )


def accident_details(request, accident_id):
    accident = get_object_or_404(Accident, pk=accident_id)
    logs = accident.logs.defer('content').all()
    return render_to_response(
        'ceburasko/accident_details.html',
        {
            'accident': accident,
            'logs': logs,
        },
        context_instance=RequestContext(request)
    )


def issue_modify(request, issue_id):
    issue = get_object_or_404(Issue, pk=issue_id)
    issue.title = request.POST['title']
    issue.save_logs = 'save_logs' in request.POST
    # issue.description = request.POST['description']
    issue.priority = request.POST['priority']
    if request.POST['fixed_version']:
        issue.fixed_version = Version(request.POST['fixed_version'])
    else:
        issue.fixed_version = None
        issue.is_fixed = False
    for tracker in ForeignTracker.objects.all():
        if 'tracker%d' % tracker.id in request.POST:
            if request.POST['tracker%d' % tracker.id]:
                key = request.POST['tracker%d' % tracker.id]
                issue.foreignissue_set.update_or_create(tracker=tracker, defaults={
                    'key': key,
                })
            else:
                try:
                    foreign_issue = issue.foreignissue_set.get(tracker=tracker)
                    foreign_issue.delete()
                except ObjectDoesNotExist as e:
                    pass
    update_modified_issues([issue])
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
    build, created = p.build_set.get_or_create(version=version)
    debug_identifier = request.POST['debug_identifier']
    debug_filename = request.POST['debug_file']
    binary_id = 'breakpad:%s' % debug_identifier
    build.binary_set.update_or_create(hash=binary_id, defaults={
        'filename': debug_filename,
    })
    symbol_dir = os.path.join(
        settings.BREAKPAD_SYMBOLS_PATH,
        debug_filename,
        debug_identifier,
    )
    try:
        os.makedirs(symbol_dir)
    except:
        pass
    symbol_filename = os.path.join(symbol_dir, debug_filename + '.sym')
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

def application_log(request, application_log_id):
    log = get_object_or_404(ApplicationLog, pk=application_log_id)
    response = HttpResponse(content=log.content, content_type='application/octet-stream')
    response['Content-Disposition'] = 'attachment; filename="%s"' % (os.path.basename(log.name), )
    return response
