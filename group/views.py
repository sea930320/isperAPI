from django.shortcuts import render
from utils.request_auth import auth_check
import logging
from django.http import HttpResponse
import json
from utils import code, const, public_fun, tools
from django.core.paginator import Paginator, EmptyPage
from django.db.models import Q
from django.contrib.auth.hashers import (
    check_password, is_password_usable, make_password,
)
from group.models import AllGroups
from account.models import Tuser, TRole, OfficeItems, TCompany, TCompanyType
from django.forms.models import model_to_dict
from utils.permission import permission_check

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
            qs = AllGroups.objects.filter(Q(name__icontains=search)).order_by('-id')
        else:
            qs = AllGroups.objects.all().order_by('-id')

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
                groupManager = [{'id': item.id, 'name': item.username, 'description': item.comment} for item in flow.groupManagers.all().order_by('-id')]
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
        logger.exception('get_groups_list Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


def create_new_group(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        if AllGroups.objects.filter(name=request.POST.get("name")).count() > 0:
            resp = code.get_msg(code.SUCCESS)
            resp['d'] = {'results': 'nameError'}
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        if int(request.POST.get("default")) == 1:
            AllGroups.objects.filter(default=1).update(default=0)

        NewGroup = AllGroups(
            name=request.POST.get("name", ''),
            comment=request.POST.get("comment", ''),
            default=int(request.POST.get("default", 0)),
            publish=int(request.POST.get("publish", 1))
        )
        NewGroup.save()
        TCompany(
            name='DEFAULT-COMPANY',
            comment='This is default Group',
            group=NewGroup,
            created_by=Tuser.objects.get(id=request.session['_auth_user_id']),
            companyType=TCompanyType.objects.get(id=1),
            is_default=1
        ).save()
        order = int(request.POST.get("order", 0))
        if order == 0:
            newUser = NewGroup.groupManagers.create(
                username=request.POST.get("managerName", ''),
                password=make_password(request.POST.get("managerPass", None)),
                is_superuser=0,
                gender=1,
                name='',
                comment='',
                identity=1,
                type=1,
                is_active=1,
                is_admin=0,
                director=0,
                manage=0,
                update_time='',
                del_flag=0,
                is_register=0
            )
            newUser.roles.add(TRole.objects.get(id=2))
        elif order == 1:
            NewGroup.groupManagers.add(Tuser.objects.get(username=request.POST.get("managerName")))
            Tuser.objects.get(username=request.POST.get("managerName")).roles.add(TRole.objects.get(id=2))
        elif order == 2:
            Tuser.objects.get(username=request.POST.get("managerName")).allgroups_set.clear()
            Tuser.objects.get(username=request.POST.get("managerName")).allgroups_set.add(NewGroup)

        resp = code.get_msg(code.SUCCESS)
        resp['d'] = {'results': 'success'}
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('create_new_group Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


def delete_selected_group(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        selected = eval(request.POST.get("ids", ''))
        newDefault = request.POST.get("newDefault", None)

        if newDefault != u'':
            AllGroups.objects.filter(id=newDefault).update(default=1)

        targets = AllGroups.objects.filter(id__in=selected)
        Tuser.objects.filter(id__in=targets.values_list('groupManagers')).delete()
        targets.delete()

        resp = code.get_msg(code.SUCCESS)
        resp['d'] = {'results': 'success'}
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('delete_selected_group Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


def update_group(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        id = request.POST.get("id", '')
        name = request.POST.get("name", '')
        comment = request.POST.get("comment", '')
        default = int(request.POST.get("default", 0))
        publish = int(request.POST.get("publish", 1))
        newDefault = request.POST.get("newDefault", None)

        if int(request.POST.get("default")) == 1:
            AllGroups.objects.filter(default=1).update(default=0)

        if AllGroups.objects.get(id=id).name != name:
            if AllGroups.objects.filter(name=request.POST.get("name")).count() > 0:
                resp = code.get_msg(code.SUCCESS)
                resp['d'] = {'results': 'nameError'}
                return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        AllGroups.objects.filter(id=id).update(name=name, comment=comment, default=default, publish=publish)

        if newDefault != u'':
            AllGroups.objects.filter(id=newDefault).update(default=1)

        resp = code.get_msg(code.SUCCESS)
        resp['d'] = {'results': 'success'}
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('update_group Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


def group_add_manager(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        groupID = request.POST.get("groupID", '')
        name = request.POST.get("data[name]", '')
        description = request.POST.get("data[description]", '')
        password = request.POST.get("data[password]", None)
        order = int(request.POST.get("order", 0))

        if order == 0:
            newUser = AllGroups.objects.get(id=groupID).groupManagers.create(
                username=name,
                password=make_password(password),
                is_superuser=0,
                gender=1,
                comment=description,
                identity=1,
                type=1,
                is_active=1,
                is_admin=0,
                director=0,
                manage=0,
                update_time='',
                del_flag=0,
                is_register=0
            )
            newUser.roles.add(TRole.objects.get(id=2))
        elif order == 1:
            AllGroups.objects.get(id=groupID).groupManagers.add(Tuser.objects.get(username=name))
            Tuser.objects.get(username=name).roles.add(TRole.objects.get(id=2))
        elif order == 2:
            Tuser.objects.get(username=name).allgroups_set.clear()
            Tuser.objects.get(username=name).allgroups_set.add(AllGroups.objects.get(id=groupID))

        resp = code.get_msg(code.SUCCESS)
        resp['d'] = {'results': 'success'}
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('group_add_manager Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

def group_add_assistant(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        groupID = request.POST.get("group_id", None)
        name = request.POST.get("name", None)
        password = request.POST.get("password", None)
        if all([groupID, name, password]):
            if Tuser.objects.filter(username=name).count() > 0:
                resp = code.get_msg(code.USER_EXIST)
                return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

            newUser = AllGroups.objects.get(id=groupID).groupManagerAssistants.create(
                username=name,
                password=make_password(password),
                is_superuser=0,
                gender=1,
                identity=1,
                type=1,
                is_active=1,
                is_admin=0,
                director=0,
                manage=0,
                update_time='',
                del_flag=0,
                is_register=0
            )
            newUser.roles.add(TRole.objects.get(id=6))
            resp = code.get_msg(code.SUCCESS)
            resp['d'] = {'results': 'success'}

        else:
            resp = code.get_msg(code.PARAMETER_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('group_add_manager Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


def group_update_manager(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        id = request.POST.get("id", None)
        description = request.POST.get("description", '')

        Tuser.objects.filter(id=id).update(comment=description)

        resp = code.get_msg(code.SUCCESS)
        resp['d'] = {'results': 'success'}
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('group_update_manager Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


def group_reset_manager(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        id = request.POST.get("id", None)
        password = request.POST.get("password", None)

        Tuser.objects.filter(id=id).update(password=make_password(password))

        resp = code.get_msg(code.SUCCESS)
        resp['d'] = {'results': 'success'}
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('group_reset_manager Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


def get_own_group(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        login_type = request.session['login_type']
        if login_type not in [2, 6]:
            resp = code.get_msg(code.PERMISSION_DENIED)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        id = request.user.id
        group = AllGroups.objects.get(groupManagers=id) if login_type == 2 else request.user.allgroups_set_assistants.get()
        groupInstructors = [{'id': instructor.id, 'name': instructor.username,
                             'instructorItems': [{'id': item.id, 'text': item.name} for item in
                                                 instructor.instructorItems.all()]} for instructor in
                            group.groupInstructors.all().order_by('-id')]

        result = [{
            'id': group.id,
            'name': group.name,
            'created': str(group.created),
            'instructors': groupInstructors
        }]

        resp = code.get_msg(code.SUCCESS)
        resp['d'] = {'results': result}
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('get_own_group Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


def get_instructor_items(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        groupInstructors = [{'id': item.id, 'text': item.name} for item in OfficeItems.objects.all()]

        resp = code.get_msg(code.SUCCESS)
        resp['d'] = {'results': groupInstructors}
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('get_instructor_items Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


def set_instructors(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
    if not permission_check(request, 'code_configure_instructor_group_company'):
        resp = code.get_msg(code.PERMISSION_DENIED)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
    try:
        id = request.POST.get("id", None)
        items = eval(request.POST.get("items", '[]'))
        user = Tuser.objects.get(id=id)
        user.instructorItems.clear()
        user.instructorItems.add(*OfficeItems.objects.filter(id__in=items))

        resp = code.get_msg(code.SUCCESS)
        resp['d'] = {'results': 'success'}
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('set_instructors Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


def create_instructors(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
    if not permission_check(request, 'code_configure_instructor_group_company'):
        resp = code.get_msg(code.PERMISSION_DENIED)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        id = request.POST.get("id", None)
        name = request.POST.get("data[name]", None)
        password = request.POST.get("data[password]", None)
        newInstructor = AllGroups.objects.get(id=id).groupInstructors.create(
            username=name,
            password=make_password(password),
            is_superuser=0,
            gender=1,
            name='',
            comment='',
            identity=1,
            type=1,
            is_active=1,
            is_admin=0,
            director=0,
            manage=0,
            update_time='',
            del_flag=0,
            is_register=0
        )
        newInstructor.roles.add(TRole.objects.get(id=4))

        resp = code.get_msg(code.SUCCESS)
        resp['d'] = {'results': 'success'}
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('create_instructors Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


# Company Action API


def get_company_list(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        search = request.POST.get("search", None)
        page = int(request.POST.get("page", 1))
        size = int(request.POST.get("size", const.ROW_SIZE))
        user = request.user
        login_type = request.session['login_type']
        if login_type not in [2, 6]:
            resp = code.get_msg(code.PERMISSION_DENIED)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        if search:
            data = TCompany.objects.filter(Q(name__icontains=search) & Q(
                group=user.allgroups_set.get().id if login_type == 2 else user.allgroups_set_assistants.get().id))
        else:
            data = TCompany.objects.filter(
                group=user.allgroups_set.get().id if login_type == 2 else user.allgroups_set_assistants.get().id)

        data = data.filter(is_default=0).order_by('-id')

        if len(data) == 0:
            resp = code.get_msg(code.SUCCESS)
            resp['d'] = {'results': [], 'paging': {}}
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
        else:
            paginator = Paginator(data, size)

            try:
                flows = paginator.page(page)
            except EmptyPage:
                flows = paginator.page(1)

            result = [{
                'id': item.id,
                'name': item.name,
                'type': item.companyType.name,
                'creator': item.created_by.username,
                'create_time': str(item.create_time),
                'companyManagers': [{
                    'id': user.tuser.id,
                    'name': user.tuser.username,
                    'description': user.tuser.comment
                } for user in item.tcompanymanagers_set.all().order_by('-id')],
            } for item in flows]

            paging = {
                'count': paginator.count,
                'has_previous': flows.has_previous(),
                'has_next': flows.has_next(),
                'num_pages': paginator.num_pages,
                'cur_page': flows.number,
            }

            cTypes = [{'value': item.name, 'text': item.name} for item in TCompanyType.objects.all()]

            resp = code.get_msg(code.SUCCESS)
            resp['d'] = {'results': result, 'paging': paging, 'cTypes': cTypes}
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('get_company_list Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


def create_new_company(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    if not permission_check(request, 'code_create_delete_company_group_company'):
        resp = code.get_msg(code.PERMISSION_DENIED)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
    try:
        name = request.POST.get("name", None)
        ctype = request.POST.get("type", None)
        comment = request.POST.get("comment", None)
        cManagerName = request.POST.get("cManagerName", None)
        cManagerPass = request.POST.get("cManagerPass", None)
        login_type = request.session['login_type']
        user = request.user
        if TCompany.objects.filter(
                Q(group=user.allgroups_set.get() if login_type == 2 else user.allgroups_set_assistants.get()) & Q(
                    name=request.POST.get("name"))).count() > 0:
            resp = code.get_msg(code.SUCCESS)
            resp['d'] = {'results': 'nameError'}
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        if Tuser.objects.filter(username=request.POST.get("cManagerName")).count() > 0:
            resp = code.get_msg(code.SUCCESS)
            resp['d'] = {'results': 'managerNameError'}
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        newCompany = TCompany(
            name=name,
            comment=comment,
            group=user.allgroups_set.get() if login_type == 2 else user.allgroups_set_assistants.get(),
            created_by=user,
            companyType=TCompanyType.objects.get(name=ctype)
        )
        newCompany.save()
        newCManager = newCompany.tuser_set.create(
            username=cManagerName,
            password=make_password(cManagerPass),
            is_superuser=0,
            gender=1,
            name='',
            comment='',
            identity=1,
            type=1,
            is_active=1,
            is_admin=0,
            director=0,
            manage=0,
            update_time='',
            del_flag=0,
            is_register=0
        )
        newCompany.tcompanymanagers_set.create(tuser=newCManager)
        newCManager.roles.add(TRole.objects.get(id=3))

        resp = code.get_msg(code.SUCCESS)
        resp['d'] = {'results': 'success'}
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('create_new_company Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


def delete_selected_company(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
    if not permission_check(request, 'code_create_delete_company_group_company'):
        resp = code.get_msg(code.PERMISSION_DENIED)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
    try:
        selected = eval(request.POST.get("ids", ''))
        targets = TCompany.objects.filter(id__in=selected)
        Tuser.objects.filter(id__in=targets.values_list('tuser')).delete()
        targets.delete()

        resp = code.get_msg(code.SUCCESS)
        resp['d'] = {'results': 'success'}
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('delete_selected_company Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


def update_company(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    if not permission_check(request, 'code_company_edit_group_company'):
        resp = code.get_msg(code.PERMISSION_DENIED)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        id = request.POST.get("id", '')
        name = request.POST.get("name", '')
        type = request.POST.get("type", '')
        login_type = request.session['login_type']
        user = request.user

        if TCompany.objects.filter(Q(group=user.allgroups_set.get() if login_type == 2 else user.allgroups_set_assistants.get()) & Q(name=name) & Q(companyType__name=type)).count() > 0:
            resp = code.get_msg(code.SUCCESS)
            resp['d'] = {'results': 'nameError'}
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        TCompany.objects.filter(id=id).update(name=name, companyType=TCompanyType.objects.get(name=type))

        resp = code.get_msg(code.SUCCESS)
        resp['d'] = {'results': 'success'}
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('update_company Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


def add_company_manager(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
    if not permission_check(request, 'code_company_edit_group_company'):
        resp = code.get_msg(code.PERMISSION_DENIED)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
    try:
        companyID = request.POST.get("companyID", '')
        name = request.POST.get("data[name]", '')
        description = request.POST.get("data[description]", '')
        password = request.POST.get("data[password]", None)

        if Tuser.objects.filter(username=request.POST.get("data[name]")).count() > 0:
            resp = code.get_msg(code.SUCCESS)
            resp['d'] = {'results': 'managerNameError'}
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        newUser = TCompany.objects.get(id=companyID).tuser_set.create(
            username=name,
            password=make_password(password),
            is_superuser=0,
            gender=1,
            comment=description,
            identity=1,
            type=1,
            is_active=1,
            is_admin=0,
            director=0,
            manage=0,
            update_time='',
            del_flag=0,
            is_register=0
        )
        TCompany.objects.get(id=companyID).tcompanymanagers_set.create(tuser=newUser)
        newUser.roles.add(TRole.objects.get(id=3))

        resp = code.get_msg(code.SUCCESS)
        resp['d'] = {'results': 'success'}
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('add_company_manager Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

def add_company_assistant(request):

    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        companyID = request.POST.get("company_id", None)
        name = request.POST.get("name", None)
        password = request.POST.get("password", None)
        if all([companyID, name, password]):
            if Tuser.objects.filter(username=name).count() > 0:
                resp = code.get_msg(code.USER_EXIST)
                return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

            newUser = TCompany.objects.get(id=companyID).assistants.create(
                username=name,
                password=make_password(password),
                is_superuser=0,
                gender=1,
                identity=1,
                type=1,
                is_active=1,
                is_admin=0,
                director=0,
                manage=0,
                update_time='',
                del_flag=0,
                is_register=0
            )
            newUser.roles.add(TRole.objects.get(id=7))
            resp = code.get_msg(code.SUCCESS)
            resp['d'] = {'results': 'success'}

        else:
            resp = code.get_msg(code.PARAMETER_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('group_add_manager Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

def update_company_manager(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
    if not permission_check(request, 'code_company_edit_group_company'):
        resp = code.get_msg(code.PERMISSION_DENIED)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
    try:
        id = request.POST.get("id", None)
        description = request.POST.get("description", '')

        Tuser.objects.filter(id=id).update(comment=description)

        resp = code.get_msg(code.SUCCESS)
        resp['d'] = {'results': 'success'}
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('update_company_manager Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


def reset_company_manager(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
    if not permission_check(request, 'code_company_edit_group_company'):
        resp = code.get_msg(code.PERMISSION_DENIED)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
    try:
        id = request.POST.get("id", None)
        password = request.POST.get("password", None)

        Tuser.objects.filter(id=id).update(password=make_password(password))

        resp = code.get_msg(code.SUCCESS)
        resp['d'] = {'results': 'success'}
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('reset_company_manager Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


def get_groups_all_list(request):
    resp = auth_check(request, "GET")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        if request.session['login_type'] not in [1, 2, 6]:
            resp = code.get_msg(code.PERMISSION_DENIED)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
        groups = AllGroups.objects.all()
        results = []
        for group in groups:
            result = model_to_dict(group, fields=['id', 'name'])
            result['companies'] = [model_to_dict(company, fields=['id', 'name']) for company in
                                   group.tcompany_set.all()]
            results.append(result)
        resp = code.get_msg(code.SUCCESS)
        resp['d'] = {'results': results}
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    except Exception as e:
        logger.exception('get_groups_all_list Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")


def check_user_group(request):
    resp = auth_check(request, "POST")
    if resp != {}:
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

    try:
        if request.session['login_type'] != 1:
            resp = code.get_msg(code.PERMISSION_DENIED)
            return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")

        username = request.POST.get("username", None)
        before = ''

        if len(Tuser.objects.filter(username=username)) == 0:
            results = 0
        elif len(Tuser.objects.filter(Q(username=username) & Q(roles__id__in=[2]))) > 0:
            results = 2
            before = Tuser.objects.filter(Q(username=username) & Q(roles__id__in=[2])).get().allgroups_set.get().name
        elif len(Tuser.objects.filter(Q(username=username) & ~Q(roles__id__in=[2]))) > 0:
            results = 1

        resp = code.get_msg(code.SUCCESS)
        resp['d'] = {'results': results, 'before': before}
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
    except Exception as e:
        logger.exception('get_groups_all_list Exception:{0}'.format(str(e)))
        resp = code.get_msg(code.SYSTEM_ERROR)
        return HttpResponse(json.dumps(resp, ensure_ascii=False), content_type="application/json")
