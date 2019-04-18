from django.shortcuts import render
from utils.request_auth import auth_check
import logging
from django.http import HttpResponse
import json
from utils import code, const, public_fun, tools
from django.db.models import Q
from group.models import Groups

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
            qs = Groups.objects.filter(Q(name__icontains=search))
        else:
            qs = Groups.objects.all()

        # if request.session['login_type'] == 1:
            # users = GroupManagers.objects.all()
            # ids = [item.id for item in users]
            # for group in qs:
            #     print group.groupManager_ids
            # print (ids)

            # paginator = Paginator(qs, size)
            #
            # try:
            #     flows = paginator.page(page)
            # except EmptyPage:
            #     flows = paginator.page(1)
            #
            # results = []
            # for flow in flows:
            #     user_info = user_simple_info(flow.created_by)
            #     if user_info is None:
            #         user_info = {}
            #     results.append({
            #         'id': flow.id, 'name': flow.name, 'xml': flow.xml, 'animation1': file_info(flow.animation1),
            #         'animation2': file_info(flow.animation2), 'status': flow.status, 'type_label': flow.type_label,
            #         'task_label': flow.task_label, 'create_time': flow.create_time.strftime('%Y-%m-%d'),
            #         'step': flow.step, 'created_by': user_info, 'protected': flow.protected, 'is_share': flow.is_share
            #     })

            # paging = {
            #     'count': paginator.count,
            #     'has_previous': flows.has_previous(),
            #     'has_next': flows.has_next(),
            #     'num_pages': paginator.num_pages,
            #     'cur_page': flows.number,
            # }
            #
            # resp = code.get_msg(code.SUCCESS)
            # resp['d'] = {'results': results, 'paging': paging}
            # return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('api_workflow_list Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
