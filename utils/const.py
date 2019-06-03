# -*- coding: utf-8 -*-
DELETE_FLAG_NO = 0
DELETE_FLAG_YES = 1
# WEB_HOST = 'http://121.42.178.20:8012'
WEB_HOST = 'http://lets.whhuiyu.com'
# 每页数据量
ROW_SIZE = 10

# 默认用户密码
PASSWORD_DEFAULT = '123456'

DEVICE = {
    1: u'android',
    2: u'ios',
    3: u'wechat',
}

DEVICE_WEB = 0
DEVICE_ANDROID = 1
DEVICE_IOS = 2

MSG_TYPE_TXT = 'txt'
MSG_TYPE_AUDIO = 'audio'
MSG_TYPE_CMD = 'cmd'

# 性别
GENDER = (
    (1, u'男'),
    (2, u'女'),
)

# 用户身份
USER_TYPE = (
    (1, u'学生'),
    (2, u'老师')
)
USER_TYPE_STUDENT = 1
USER_TYPE_TEACHER = 2

# 身份
IDENTITY = (
    (1, u'实验人员'),
    (2, u'实验指导'),
    (3, u'系统管理员'),
    (4, u'超级管理员')
)

# 流程状态
FLOW_STATUS = (
    (1, u'未发布'),
    (2, u'已发布'),
)

EXPERIMENT_TYPE = (
    (1, u'立法实验'),
    (2, u'执法实验'),
    (3, u'诉讼与仲裁实验'),
    (4, u'非诉业务实验'),
    (5, u'法律实效评价实验'),
    (6, u'证据学实验'),
    (7, u'法律思维实验'),
    (8, u'自由类型实验'),
)

# 方向
DIRECTION = (
    (1, u'正'),
    (2, u'背'),
    (3, u'侧'),
)

# 程序模块类型
PROCESS_TYPE = (
    (1, u'动画'),
    (2, u'编辑'),
    (3, u'展示'),
    (4, u'心得'),
    (5, u'投票'),
    (6, u'跳转')
)
PROCESS_FLASH_TYPE = 1
PROCESS_EDIT_TYPE = 2
PROCESS_SHOW_TYPE = 3
PROCESS_EXPERIENCE_TYPE = 4
PROCESS_VOTE_TYPE = 5
PROCESS_JUMP_TYPE = 6

DOC_USAGE = (
    (0, u'无'),
    (1, u'操作指南'),
    (2, u'关联文件'),
    (3, u'模版'),
    (4, u'材料'),
    (5, u'公文'),
    (6, u'成果参考'),
    (7, u'项目提示'),
)

FLOW_DOC_TEMPLATE_USAGE = 3

ROLE_CATEGORY = (
    (1, u'律师'),
    (2, u'法官'),
    (3, u'公务员'),
    (4, u'检察官'),
    (5, u'公证员'),
    (6, u'立法者'),
    (99, u'其他'),
)

# 成果参考释放方式
PROJECT_REFERENCE = (
    (1, u'同步'),
    (2, u'后步'),
    (3, u'最后'),
)

# 申请为公共项目状态
PROJECT_PUBLIC = (
    (1, u'申请'),
    (2, u'不申请'),
)

# 申请为公共项目状态
PROJECT_ALL_ROLE = (
    (1, u'永许'),
    (2, u'不永许'),
)

# 实验层次
PROJECT_LEVEL = (
    (1, u'*'),
    (2, u'**'),
    (3, u'***'),
    (4, u'****'),
    (5, u'*****'),
)

# 流程图完整显示
PROJECT_ENTIRE_GRAPH = (
    (1, u'完整显示'),
    (2, u'逐步显示'),
    (3, u'不显示'),
)

# 是否允许重做
PROJECT_CAN_REDO = (
    (1, u'永许'),
    (2, u'不永许'),
)

# 开放模式
PROJECT_IS_OPEN = (
    (1, u'自由'),
    (2, u'限时'),
    (3, u'指定用户'),
)

# 能力目标
PROJECT_ABILITY_TARGET = (
    (1, u'简易'),
    (2, u'基础'),
    (3, u'进阶'),
    (4, u'综合'),
    (5, u'创新'),
)

# 是否开放邀请
TEAM_OPEN_JOIN = (
    (1, u'开放'),
    (2, u'不开放'),
)

BUSINESS_WAITING = 1
BUSINESS_PROCESSING = 2
BUSINESS_FINISHED = 9

BUSINESS_STATUS = (
    (1, u'等待中'),
    (2, u'进行中'),
    (9, u'已结束'),
)

# 实验任务状态
EXPERIMENT_WAITING = 1
EXPERIMENT_PROCESSING = 2
EXPERIMENT_FINISHED = 9

EXPERIMENT_STATUS = (
    (1, u'等待中'),
    (2, u'进行中'),
    (9, u'已结束'),
)

# 实验表达管理状态
EXPERIMENT_CONTROL_STATUS = (
    (1, u'未启动'),
    (2, u'启动'),
)
# 实验环节投票状态
EXPERIMENT_VOTE_STATUS = (
    (1, u'进行中'),
    (2, u'已结束'),
)

# 带入带出状态
COME_STATUS = (
    (1, u'待带入'),
    (2, u'待送出'),
    (9, u'普通状态'),
)

# 入席退席状态
SITTING_STATUS = (
    (1, u'未入席'),
    (2, u'已入席'),
)
SITTING_UP_STATUS = 1
SITTING_DOWN_STATUS = 2

SCHEDULE_STATUS = (
    (0, u'初始'),
    (1, u'安排'),
    (2, u'上位'),
)
SCHEDULE_INIT_STATUS = 0
SCHEDULE_OK_STATUS = 1
SCHEDULE_UP_STATUS = 2

TRUE = 1
FALSE = 0

SEAT_TYPE = (
    (0, u'普通'),
    (1, u'报告席'),
)
SEAT_REPORT_TYPE = 1

# 起立坐下状态
STAND_STATUS = (
    (1, u'起立'),
    (2, u'坐下'),
)

# 实验文件提交状态
SUBMIT_STATUS = (
    (1, u'未提交'),
    (2, u'已提交'),
    (9, u'未处理'),
)

# 实验文件提交状态
VOTE_STATUS = (
    (0, u'未投票'),
    (1, u'同意'),
    (2, u'不同意'),
    (9, u'弃权'),
)

# 实验文件展示状态
SHOW_STATUS = (
    (1, u'已同意'),
    (2, u'未同意'),
    (9, u'未处理'),
)

# 实验文件签字状态
SIGN_STATUS = (
    (0, u'等待'),
    (1, u'已签字'),
    (2, u'拒绝签字'),
)

# 上传文件类型限制
FILE_TYPES = ['docx']

TEAM_OPEN_JOIN_YES = 1
TEAM_OPEN_JOIN_NO = 2

FILE_TYPE = (
    (0, u'文件'),
    (1, u'文档'),
    (2, u'图片'),
    (3, u'视频'),
    (4, u'音频'),
)


# 动作命令常量
ACTION_TRANS = 'action_trans'
ACTION_OK = 'action_ok'
ACTION_ROLE_BANNED = 'action_role_banned'
ACTION_ROLE_MEET = 'action_role_meet'
ACTION_ROLE_MEET_OPT = 'action_role_meet_opt'
ACTION_ROLE_APPLY_SPEAK = 'action_role_apply_speak'
ACTION_ROLE_APPLY_SPEAK_OPT = 'action_role_apply_speak_opt'
ACTION_DOC_APPLY_SHOW = 'action_doc_apply_show'
ACTION_DOC_APPLY_SHOW_OPT = 'action_doc_apply_show_opt'
ACTION_DOC_SHOW = 'action_doc_show'
ACTION_ROLE_LETOUT = 'action_role_letout'
ACTION_ROLE_LETIN = 'action_role_letin'
ACTION_ROLE_SITDOWN = 'action_role_sitdown'
ACTION_ROLE_STAND = 'action_role_stand'
ACTION_ROLE_HIDE = 'action_role_hide'
ACTION_ROLE_SHOW = 'action_role_show'
ACTION_DOC_APPLY_SUBMIT = 'action_doc_apply_submit'
ACTION_DOC_APPLY_SUBMIT_OPT = 'action_doc_apply_submit_opt'
ACTION_DOC_SUBMIT = 'action_doc_submit'
ACTION_EXP_BACK = 'action_exp_back'
ACTION_EXP_RESTART = 'action_exp_restart'
ACTION_EXP_NODE_END = 'action_exp_node_end'
ACTION_EXP_FINISH = 'action_exp_finish'
ACTION_SUBMIT_EXPERIENCE = 'action_submit_experience'
ACTION_TXT_SPEAK = 'action_txt_speak'
ACTION_ROLE_VOTE = 'action_role_vote'
ACTION_ROLE_VOTE_END = 'action_role_vote_end'
ACTION_ROLE_REQUEST_SIGN = 'action_role_request_sign'
ACTION_ROLE_SIGN = 'action_role_sign'
ACTION_ROLE_SCHEDULE_REPORT = 'action_role_schedule_report'
ACTION_ROLE_TOWARD_REPORT = 'action_role_toward_report'
ACTION_ROLE_EDN_REPORT = 'action_role_end_report'
ACTION_DOC_REFRESH = 'action_doc_refresh'

ACTION_OPT_PASS = 1
ACTION_OPT_UN_PASS = 2

ACTION_ROLES_EXIT = 'action_roles_exit'

DIRECTION_FRONT = 1
DIRECTION_BACK = 2
DIRECTION_SIDE = 3

# 表达管理启动后最大允许发言的次数
MESSAGE_MAX_TIMES = 3

# 缓存key
CACHE_EXPERIMENT_KEYS = 'experiment_key'
# 当前用户可选角色
CACHE_ROLES_STATUS_BY_USER = 'roles_status_by_user'
CACHE_ROLES_STATUS_SIMPLE_BY_USER = 'roles_status_simple_by_user'

CACHE_ROLE_PROCESS_ACTIONS = 'role_process_actions'
CACHE_ROLE_NODE_CAN_TERMINATE = 'role_node_can_terminate'
CACHE_ROLE_IMAGE = 'role_image'
CACHE_ROLE_POSITION = 'role_position'

CACHE_NODE_DOCS = 'node_docs'
CACHE_NODE_ROLE_DOCS = 'node_role_docs'
CACHE_PRE_NODE_ROLE_DOCS = 'pre_node_role_docs'
# 实验文件
CACHE_EXPERIMENT_FILE_DISPLAY = 'experiment_files'
# 所有角色
CACHE_ALL_SIMPLE_ROLES_STATUS = 'all_simple_roles_status'
CACHE_ALL_ROLES_STATUS = 'all_roles_status'
# 实验详情
CACHE_EXPERIMENT_DETAIL = 'experiment_detail'
CACHE_EXPERIMENT_PATH = 'experiment_path'

"""
流程设置步骤
"""
# 初始状态
FLOW_STEP_0 = 0
# 环节设置
FLOW_STEP_1 = 1
# 素材设置
FLOW_STEP_2 = 2
# 添加角色
FLOW_STEP_3 = 3
# 角色分配
FLOW_STEP_4 = 4
# 动作设置
FLOW_STEP_5 = 5
# 动画设置
FLOW_STEP_6 = 6
# 角色设置
FLOW_STEP_7 = 7
# 设置完成
FLOW_STEP_8 = 8

"""
项目设置步骤
"""
# 初始状态
PRO_STEP_0 = 0
# 基本信息
PRO_STEP_1 = 1
# 角色设置
PRO_STEP_2 = 2
# 素材设置
PRO_STEP_3 = 3
# 跳转
PRO_STEP_4 = 4
# 设置完成
PRO_STEP_9 = 9

"""
环节走向
"""
FLOW_FORWARD = 'forward'
FLOW_BACK = 'back'

"""
老师观察者角色类型
"""
ROLE_TYPE_OBSERVER = '老师观察者'