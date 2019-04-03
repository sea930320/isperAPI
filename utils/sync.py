#!/usr/bin/python
# -*- coding=utf-8 -*-
from account.models import Tuser
from workflow.models import *
from utils import easemob
from utils import const
from time import sleep


def sync_account():
    lst = Tuser.objects.filter(del_flag=const.DELETE_FLAG_NO)
    for user in lst:
        try:
            easemob_success, easemob_result = easemob.register_new_user(user.pk, easemob.EASEMOB_PASSWORD)
            print 'easemob register_new_user:%s,%s,%s' % (user.pk, easemob_success, easemob_result)
            sleep(0.2)
        except Exception as e:
            print "register exception：%s", str(e)
    print 'is done'


def sync_the_account(id):
    try:
        easemob_success, easemob_result = easemob.register_new_user(str(id), easemob.EASEMOB_PASSWORD)
        print 'easemob register_new_user:%s,%s,%s' % (id, easemob_success, easemob_result)
    except Exception as e:
        print "register exception：%s", str(e)
    print 'is done'


def delete_accounts():
    lst = Tuser.objects.filter(del_flag=const.DELETE_FLAG_YES)
    print lst.count()
    for user in lst:
        try:
            easemob_success, easemob_result = easemob.delete_user(user.pk)
            print 'easemob delete_the_account:%s,%s,%s' % (user.pk, easemob_success, easemob_result)
            sleep(0.2)
        except Exception as e:
            print "delete_the_account exception：%s", str(e)
    print 'is done'


def delete_the_account(id):
    try:
        easemob_success, easemob_result = easemob.delete_user(str(id))
        print 'easemob delete_the_account:%s,%s,%s' % (id, easemob_success, easemob_result)
    except Exception as e:
        print "delete_the_account exception：%s", str(e)
    print 'is done'


def roles_allocate(flow_id):
    nodes = FlowNode.objects.filter(flow_id=flow_id, del_flag=0)
    roles = FlowRole.objects.filter(flow_id=flow_id, del_flag=0)

    FlowRoleAllocation.objects.filter(flow_id=flow_id).update(del_flag=1)
    # 全选环节场景动画和功能动作
    flow_actions = []
    actions_list = FlowAction.objects.filter(del_flag=0).values_list('id', flat=True)
    for d in actions_list:
        flow_actions.append(int(d))
    print flow_actions
    print nodes.count()
    n = 1
    for node in nodes:
        can_terminate = False
        i = 1
        for role in roles:
            if i == 1:
                can_terminate = True

            a = FlowRoleAllocation.objects.filter(flow_id=flow_id, node_id=node.pk, role_id=role.pk).first()
            if a:
                FlowRoleAllocation.objects.filter(pk=a.pk).update(can_terminate=can_terminate,
                                                                  can_brought=False, del_flag=0)
            else:
                FlowRoleAllocation.objects.create(flow_id=flow_id, node_id=node.pk, role_id=role.pk,
                                                  can_terminate=can_terminate, can_brought=False)

            if node.process and node.process.type == 1:
                # 全选环节功能动作，如果不存在则创建
                b = FlowRoleActionNew.objects.filter(flow_id=flow_id, node_id=node.pk, role_id=role.pk).first()
                if b:
                    FlowRoleActionNew.objects.filter(pk=b.pk).update(actions=flow_actions, del_flag=0)
                else:
                    FlowRoleActionNew.objects.create(flow_id=flow_id, node_id=node.pk,
                                                     role_id=role.pk, actions=flow_actions)

            i += 1
            can_terminate = False
        print n
        n += 1


if __name__ == '__main__':
    roles_allocate(723)
