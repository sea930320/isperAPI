from django.shortcuts import render
from utils.request_auth import auth_check
import logging
from django.http import HttpResponse
import json
from utils import code, const, public_fun, tools
from django.core.paginator import Paginator, EmptyPage
from django.db.models import Q
from group.models import AllGroups

logger = logging.getLogger(__name__)


# Create your views here.
def get_groups_list(request):
    resp = auth_check(request, "GET")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:

        search = request.GET.get("search", None)
        page = int(request.GET.get("page", 1))
        size = int(request.GET.get("size", const.ROW_SIZE))

        if search:
            qs = AllGroups.objects.filter(Q(name__icontains=search))
        else:
            qs = AllGroups.objects.all()

        # if request.session['login_type'] == 1:
        if len(qs) == 0:
            resp = code.get_msg(code.SUCCESS)
            resp['d'] = {'results': [], 'paging': {}}
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
        else:
            paginator = Paginator(qs, size)

            try:
                flows = paginator.page(page)
            except EmptyPage:
                flows = paginator.page(1)

            results = []
            for flow in flows:
                groupManager = [{'id': item.id, 'name': item.username, 'description': item.name} for item in flow.groupManagers.all()]
                if groupManager is None:
                    groupManager = [{}]
                results.append({
                    'id': flow.id, 'name': flow.name, 'comment': flow.comment, 'publish': flow.publish,
                    'default': flow.default, 'groupManagers': groupManager
                })
            #
            paging = {
                'count': paginator.count,
                'has_previous': flows.has_previous(),
                'has_next': flows.has_next(),
                'num_pages': paginator.num_pages,
                'cur_page': flows.number,
            }

            resp = code.get_msg(code.SUCCESS)
            resp['d'] = {'results': results, 'paging': paging}
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_workflow_list Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


def create_new_group(request):
    resp = auth_check(request, "GET")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:

        search = request.GET.get("search", None)
        page = int(request.GET.get("page", 1))
        size = int(request.GET.get("size", const.ROW_SIZE))

        if search:
            qs = AllGroups.objects.filter(Q(name__icontains=search))
        else:
            qs = AllGroups.objects.all()

        # if request.session['login_type'] == 1:
        if len(qs) == 0:
            resp = code.get_msg(code.SUCCESS)
            resp['d'] = {'results': [], 'paging': {}}
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
        else:
            paginator = Paginator(qs, size)

            try:
                flows = paginator.page(page)
            except EmptyPage:
                flows = paginator.page(1)

            results = []
            for flow in flows:
                groupManager = [{'id': item.id, 'name': item.username, 'description': item.name} for item in flow.groupManagers.all()]
                if groupManager is None:
                    groupManager = [{}]
                results.append({
                    'id': flow.id, 'name': flow.name, 'comment': flow.comment, 'publish': flow.publish,
                    'default': flow.default, 'groupManagers': groupManager
                })
            #
            paging = {
                'count': paginator.count,
                'has_previous': flows.has_previous(),
                'has_next': flows.has_next(),
                'num_pages': paginator.num_pages,
                'cur_page': flows.number,
            }

            resp = code.get_msg(code.SUCCESS)
            resp['d'] = {'results': results, 'paging': paging}
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_workflow_list Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
