#!/usr/bin/python
# -*- coding: utf-8 -*-


from utils import code
from group.models import TGroupManagerAssistants
from account.models import TCompanyManagerAssistants
from django.db.models import Q

def permission_check(request, action_code_name):
    login_type = request.session['login_type']
    user = request.user
    if login_type == 6:
        group = user.allgroups_set_assistants.get()  # get group that this user belongs to
        assistant_relation = TGroupManagerAssistants.objects.get(all_groups=group, tuser=user)
        return assistant_relation.actions.filter(Q(codename=action_code_name)).exists()
    if login_type == 7:
        company = user.t_company_set_assistants.get()
        assistant_relation = TCompanyManagerAssistants.objects.get(tcompany=company, tuser=user)
        return assistant_relation.actions.filter(Q(codename=action_code_name)).exists()
    return True

