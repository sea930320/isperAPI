#!/usr/bin/python
# -*- coding=utf-8 -*-

# 成功
SUCCESS = 0
# 系统错误
SYSTEM_ERROR = 500
# 权限不足
PERMISSION_DENIED = 403
# 参数错误
PARAMETER_ERROR = 400
# 请求方法错误
METHOD_NOT_ALLOW = 405
# 用户已存在
USER_EXIST = 10000
# 用户不存在
USER_NOT_EXIST = 10001
# 用户名或密码错误
USERNAME_OR_PASSWORD_ERROR = 10002
# 用户未登录
USER_NOT_LOGGED_IN = 10003
# 不是实验人员
# 不是实验指导
# 不是系统管理员
# 不是超级管理员
# 上传文件格式只支持docx格式
UPLOAD_FILE_EXT_ERROR = 10004
# 上传文件名长度过长
UPLOAD_FILE_NAME_TOOLONG_ERROR = 10005

PHONE_NOT_VERIFIED = 10006

# 流程不存在
FLOW_NOT_EXIST = 20001
# 流程已经发布
FLOW_HAS_PUBLISHED = 20002
# 流程素材不存在
FLOW_DOC_NOT_EXIST = 20003
# 流程角色不存在
FLOW_ROLE_NOT_EXIST = 20004
# 同名流程已经存在
FLOW_SAME_NAME_HAS_EXIST = 20005
# 流程图错误
FLOW_CHART_ERROR = 20006
# 流程走向错误
FLOW_DIRECTION_ERROR = 20007
# 流程程序模块设置
FLOW_PROCESS_NOT_EXIST = 20008
# 流程角色已使用，无法删除
FLOW_ROLE_HAS_USE = 20009
# 结束环节类型必须为实验报告类型
FLOW_END_NODE_MUST_REPORT_TYPE = 20010
# 操作指南导入失败
FLOW_OPT_DOC_IMPORT_FAIL = 20011
# 每个环节只能有一个操作指南
FLOW_OPT_DOC_ONLY_ONE = 20012

# 项目不存在
PROJECT_NOT_EXIST = 30001
# 项目名称已存在
PROJECT_NAME_HAS_EXIST = 30002
# 跳转项目不能设置自身
PROJECT_JUMP_CANNOT_SETUP_SELF = 30003
# 跳转项目已创建实验
PROJECT_JUMP_HAS_USE = 30004

# 小组名称已存在
TEAM_HAS_EXIST = 40001
# 小组已参加实验
TEAM_HAS_JOIN_EXP = 40002
# 没有小组操作权限
TEAM_HAS_NOT_PERM = 40003
# 小组不存在
TEAM_NOT_EXIST = 40004
# 小组成员不存在
TEAM_MEMBER_NOT_EXIST = 40005
# 小组组长不能删除自己
TEAM_CANNOT_DELETE_SELF = 40006
# 小组成员已入席
TEAM_MEMBER_SITING = 40007

# 实验任务不存在
EXPERIMENT_NOT_EXIST = 50001
# 实验任务已经开始
EXPERIMENT_HAS_STARTED = 50002
# 实验环节错误
EXPERIMENT_NODE_ERROR = 50003
# 实验任务已经结束
EXPERIMENT_HAS_FINISHED = 50004
# 实验未开始
EXPERIMENT_HAS_NOT_STARTED = 50005
# 实验当前处于第一个环节
EXPERIMENT_IN_FIRST_NODE = 50006
# 角色分配错误
EXPERIMENT_ROLE_ALLOCATE_ERROR = 50007
# 当前环节不存在该角色
EXPERIMENT_NODE_ROLE_NOT_EXIST = 50008
# 当前该角色形象不存在
EXPERIMENT_ROLE_IMAGE_NOT_EXIST = 50009
# 当前该角色实验心得已提交
EXPERIMENT_EXPERIENCE_HAS_EXIST = 50010
# 当前该角色实验心得还没提交
EXPERIMENT_EXPERIENCE_USER_NOT_SUBMIT = 50011
# 实验任务启动失败
EXPERIMENT_START_FAILED = 50012
# 实验操作权限
EXPERIMENT_PERMISSION_DENIED = 50013
# 角色占位缺失
EXPERIMENT_ROLE_POSITION_NOT_EXIST = 50014
# 站位已有人
EXPERIMENT_POSITION_HAS_USE = 50015
# 角色已入席
EXPERIMENT_ROLE_HAS_IN_POSITION = 50016
# 角色已投票
EXPERIMENT_ROLE_HAS_VOTE = 50017
# 投票已结束
EXPERIMENT_ROLE_VOTE_IS_END = 50018
# 投票已结束
EXPERIMENT_ROLE_VOTE_NOT_END = 50019
# 当前场景报告席配置错误，请检查相关配置
EXPERIMENT_ROLE_REPORT_ERROR = 50020
# 当前角色未安排发言
EXPERIMENT_ROLE_REPORT_SCHEDULE_ERROR = 50021
# 验证项目中是否有未配置的跳转项目
EXPERIMENT_JUMP_PROJECT_SETUP_ERROR = 50022
# 已安排签字request_sign
EXPERIMENT_HAS_REQUEST_SIGN_ERROR = 50023
# 不支持的文件类型
EXPERIMENT_FILE_TYPE_NOT_ALLOW = 50024
# 有角色未设置
EXPERIMENT_ROLE_NOT_SET = 50025
# 该实验没有注册到课堂
EXPERIMENT_NOT_REGISTER = 50026

# 消息发送失败
MESSAGE_SEND_FAILED = 60001
# 动作指令错误
MESSAGE_ACTION_ERROR = 60002
# 表达管理状态下，每次申请发言只能发言三次control
MESSAGE_SPEAKER_CONTROL = 60003
# 表达管理状态下，每次申请发言只能发言三次
MESSAGE_TIMES_USE_OUT = 60004
# 未入席不能发言
MESSAGE_SITTING_UP_CANNOT_SPEAKER = 60005

# 课程下面有学生，无法删除
MESSAGE_COURSE_STUDENT_EXISTS = 70001

#
ADVERTISING_NAME_ALREADY_EXISTS = 90001

MSG = {
    0: u'success',
    400: u'提交数据验证失败',
    403: u'权限错误',
    405: u'请求方法不允许',
    500: u'系统异常',
    10000: u'用户已存在',
    10001: u'用户不存在',
    10002: u'用户名或密码错误',
    10003: u'用户未登录',
    10004: u'文件格式错误',
    10005: u'上传文件名长度过长',
    10006: u'电话验证失败',
    20001: u'流程不存在',
    20002: u'该流程已经发布',
    20003: u'该素材不存在或已被删除',
    20004: u'角色不存在',
    20005: u'流程名已存在',
    20006: u'流程图错误，请完善流程图',
    20007: u'流程走向错误',
    20008: u'流程未完成设置程序模块',
    20009: u'该流程角色已被使用，无法删除',
    20010: u'结束环节类型必须为实验报告类型！',
    20011: u'没有可导入本流程的操作指南数据！',
    20012: u'每个环节只能有一个操作指南!',

    30001: u'项目不存在',
    30002: u'项目名称已存在',
    30003: u'跳转项目不能设置自身',
    30004: u'该项目已创建实验，无法修改跳转设置！',

    40001: u'小组名称已存在',
    40002: u'小组已参加实验,无法删除小组和成员',
    40003: u'您不是小组组长，没有操作权限！',
    40004: u'小组不存在',
    40005: u'小组成员不存在',
    40006: u'不能删除组长',
    40007: u'该成员存在实验中已经入席，不能删除',

    50001: u'实验任务不存在',
    50002: u'实验任务已开始',
    50003: u'当前实验已走向其它环节，请重新进入实验！',
    50004: u'实验任务已结束',
    50005: u'实验任务未开始',
    50006: u'实验任务当前处于第一个环节',
    50007: u'角色分配未完成或分配不正确',
    50008: u'当前实验环节不存在该角色',
    50009: u'当前该角色形象不存在',
    50010: u'当前实验该用户已提交实验心得',
    50011: u'当前实验还有未提交实验心得用户,无法结束',
    50012: u'实验任务启动失败',
    50013: u'没有实验操作权限',
    50014: u'角色站位设置不存在',
    50015: u'该站位已有角色入席',
    50016: u'该角色已入席',
    50017: u'角色已投票',
    50018: u'投票已结束',
    50019: u'投票未结束',
    50020: u'当前场景报告席配置错误，请检查相关配置',
    50021: u'当前角色未安排发言',
    50022: u'请检查项目中有是否有未配置的跳转项目',
    50023: u'已要求签字',
    50024: u'不支持的文件类型',
    50025: u'当前环节还有角色没有设置',
    50026: u'该实验没有注册到课堂',

    60001: u'消息发送失败',
    60002: u'动作指令错误',
    60003: u'实验当前环节启动了表达管理，禁止发言',
    60004: u'表达管理中,每次申请发言只能发言三次',
    60005: u'角色未入席，不能执行相关操作！',

    70001: u'该课程下存在学生，不能删除该课程',

    90001: u'公告名称已存在'

}


def get_msg(code):
    return {'c': code, 'm': MSG[code]}
