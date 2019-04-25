#!/usr/bin/python
# -*- coding=utf-8 -*-

from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin

from account import views as account_views
from cms import views as cms_views
from api import views as api_views
from course import views as course_views
from experiment import views as experiment_views
from project import views as project_views
from system import views as system_views
from team import views as team_views
from workflow import views as workflow_views
from group import views as group_views

urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
]

urlpatterns += (
    url(r'^api/account/query$', account_views.api_account_query),
    url(r'^api/account/users/$', account_views.api_account_users),
    url(r'^api/account/logout$', account_views.api_account_logout),
    url(r'^api/account/login$', account_views.api_account_login),
    url(r'^api/account/send/code', account_views.api_account_send_verify_code),
    url(r'^api/account/users/v3/$', account_views.api_account_users_v3),
    url(r'^api/account/companys/$', account_views.api_account_companys),
    url(r'^api/account/classes/$', account_views.api_account_classes),
    url(r'^api/account/user/update$', account_views.api_account_user_update),
    url(r'^api/account/password/update$', account_views.api_account_password_update),
    url(r'^api/account/avatar-img/update', account_views.api_account_avatar_img_update),
    url(r'^api/account/avatar-img/upload', account_views.api_account_avatar_img_upload),
    url(r'^api/account/user/save$', account_views.api_account_user_save),
    url(r'^api/account/user/create', account_views.api_account_user_create),
    url(r'^api/account/get/user/$', account_views.api_account_get_user),
    url(r'^api/account/import$', account_views.api_account_import),
    url(r'^api/account/export$', account_views.api_account_export),
    url(r'^api/account/user/auth/update', account_views.api_account_user_auth_update),
    url(r'^api/account/user/delete', account_views.api_course_user_delete),
    url(r'^api/account/share', account_views.api_account_share),
    url(r'^api/account/default-group', account_views.api_get_default_group),
)

urlpatterns += (
    url(r'^api/cms/to/user/list$', cms_views.api_cms_to_user_list),
    url(r'^api/cms/send/msg$', cms_views.api_cms_send_msg),
    url(r'^api/cms/msg/list$', cms_views.api_cms_msg_list),
    url(r'^api/cms/new/msg/num$', cms_views.api_cms_new_msg_num),
)

urlpatterns += (
    url(r'^api/course/class/list$', course_views.api_course_class_list),
    url(r'^api/course/list$', course_views.api_course_list),
    url(r'^api/course/class/list/teacher/$', course_views.api_course_list_class_teacher),
    url(r'^api/course/student/list$', course_views.api_course_student_list),
    url(r'^api/course/delete$', course_views.api_course_delete),
    url(r'^api/course/list/v3$', course_views.api_course_list_v3),
    url(r'^api/course/student/list/export$', course_views.api_course_student_list_export),
    url(r'^api/course/class/student/v3$', course_views.api_course_class_student_v3),
    url(r'^api/course/class/update$', course_views.api_course_class_update),
    url(r'^api/course/student/list/import$', course_views.api_course_student_list_import),
    url(r'^api/course/class/student/delete$', course_views.api_course_class_student_delete),
    url(r'^api/course/student/save$', course_views.api_course_student_save),
    url(r'^api/course/share$', course_views.api_course_share),
)

urlpatterns += (
    url(r'^api/experiment/template/new$', experiment_views.api_experiment_template_new),
    url(r'^api/experiment/template/create$', experiment_views.api_experiment_template_create),
    url(r'^api/experiment/template/sign$', experiment_views.api_experiment_template_sign),
    url(r'^api/experiment/templates$', experiment_views.api_experiment_templates),
    url(r'^api/experiment/template/detail$', experiment_views.api_experiment_templates_detail),
    url(r'^api/experiment/file/display/list$', experiment_views.api_experiment_file_display_list),
    url(r'^api/experiment/doc/detail$', experiment_views.api_experiment_doc_detail),

    url(r'^api/experiment/start$', experiment_views.api_experiment_start),
    url(r'^api/experiment/delete$', experiment_views.api_experiment_delete),
    url(r'^api/experiment/update$', experiment_views.api_experiment_update),
    url(r'^api/experiment/list$', experiment_views.api_experiment_list),
    url(r'^api/experiment/detail$', experiment_views.api_experiment_detail),

    url(r'^api/experiment/node/detail$', experiment_views.api_experiment_node_detail),
    url(r'^api/experiment/node/role/docs$', experiment_views.api_experiment_node_role_docs),
    url(r'^api/experiment/node/function$', experiment_views.api_experiment_node_function),
    url(r'^api/experiment/role/out/list$', experiment_views.api_experiment_role_out_list),
    url(r'^api/experiment/role/in/list$', experiment_views.api_experiment_role_in_list),
    url(r'^api/experiment/note/list$', experiment_views.api_experiment_note_list),
    url(r'^api/experiment/note/create$', experiment_views.api_experiment_note_create),
    url(r'^api/experiment/note/detail$', experiment_views.api_experiment_note_detail),
    url(r'^api/experiment/role/status$', experiment_views.api_experiment_role_status),

    url(r'^api/experiment/docs/create$', experiment_views.api_experiment_docs_create),
    url(r'^api/experiment/docs/delete', experiment_views.api_experiment_docs_delete),
    url(r'^api/experiment/create$', experiment_views.api_experiment_create),
    url(r'^api/experiment/message/push$', experiment_views.api_experiment_message_push),
    url(r'^api/experiment/message/upload$', experiment_views.api_experiment_message_upload),
    url(r'^api/experiment/node/messages$', experiment_views.api_experiment_node_messages),
    url(r'^api/experiment/messages$', experiment_views.api_experiment_messages),

    url(r'^api/experiment/experience/save$', experiment_views.api_experiment_save_experience),
    url(r'^api/experiment/experience/list$', experiment_views.api_experiment_experience_list),
    url(r'^api/experiment/experience/detail$', experiment_views.api_experiment_experience_detail),
    url(r'^api/experiment/trans/path$', experiment_views.api_experiment_trans_path),
    url(r'^api/experiment/node/path$', experiment_views.api_experiment_node_path),
    url(r'^api/experiment/node/path/messages$', experiment_views.api_experiment_path_messages),

    url(r'^api/experiment/node/docs$', experiment_views.api_experiment_node_docs),
    url(r'^api/experiment/jump/start$', experiment_views.api_experiment_jump_start),
    url(r'^api/experiment/role/report/list$', experiment_views.api_experiment_role_schedule_report_list),
    url(r'^api/experiment/request/sign/roles$', experiment_views.api_experiment_request_sign_roles),
    url(r'^api/experiment/node/vote/status$', experiment_views.api_experiment_vote_status),

    url(r'^api/experiment/report/generate$', experiment_views.api_experiment_report_generate),
    url(r'^api/experiment/result$', experiment_views.api_experiment_result),

    url(r'^api/experiment/teacher/list$', experiment_views.api_experiment_teacher_list),
    url(r'^api/experiment/evaluate/list$', experiment_views.api_experiment_evaluate_list),
    url(r'^api/experiment/evaluate$', experiment_views.api_experiment_evaluate),
    url(r'^api/experiment/node/evaluate', experiment_views.api_experiment_node_evaluate),
    url(r'^api/experiment/evaluate/user/list', experiment_views.api_experiment_evaluate_user_list),
    url(r'^api/experiment/node/list', experiment_views.api_experiment_node_list),
    url(r'^api/experiment/evaluate/detail', experiment_views.api_experiment_evaluate_detail),
)

urlpatterns += (
    url(r'^api/project/docs/allocate$', project_views.api_project_docs_allocate),
    url(r'^api/project/docs/delete$', project_views.api_project_docs_delete),
    url(r'^api/project/docs/detail$', project_views.api_project_docs_detail),
    url(r'^api/project/docs/create$', project_views.api_project_docs_create),
    url(r'^api/project/roles/detail$', project_views.api_project_roles_detail),
    url(r'^api/project/roles/configurate$', project_views.api_project_roles_configurate),
    url(r'^api/project/role/image/update$', project_views.api_project_role_image_update),
    url(r'^api/project/jump/detail$', project_views.api_project_jump_detail),
    url(r'^api/project/jump/setup$', project_views.api_project_jump_setup),
    url(r'^api/project/update$', project_views.api_project_update),
    url(r'^api/project/has_experiment$', project_views.api_project_has_experiment),
    url(r'^api/project/delete$', project_views.api_project_delete),
    url(r'^api/project/detail$', project_views.api_project_detail),
    url(r'^api/project/create$', project_views.api_project_create),
    url(r'^api/project/copy$', project_views.api_project_copy),
    url(r'^api/project/list$', project_views.api_project_list),
    url(r'^api/project/related$', project_views.api_project_related),
    url(r'^api/project/protected', project_views.api_project_protected),
    url(r'^api/project/share', project_views.api_project_share),
    url(r'^api/project/unshare', project_views.api_project_unshare),
)

urlpatterns += (
    url(r'^api/file/upload$', system_views.api_file_upload),
    url(r'^api/system/app/version$', system_views.api_file_upload),
)

urlpatterns += (
    url(r'^api/team/leader/set$', team_views.api_team_leader_set),
    url(r'^api/team/member/add$', team_views.api_team_member_add),
    url(r'^api/team/member/join$', team_views.api_team_member_join),
    url(r'^api/team/member/delete$', team_views.api_team_member_delete),
    url(r'^api/team/delete$', team_views.api_team_delete),
    url(r'^api/team/member$', team_views.api_team_member),
    url(r'^api/team/create$', team_views.api_team_create),
    url(r'^api/team/create/v3$', team_views.api_team_create_v3),
    url(r'^api/team/open$', team_views.api_team_open),
    url(r'^api/team/my$', team_views.api_team_my),
    url(r'^api/team/other$', team_views.api_team_other),
    url(r'^api/team/list$', team_views.api_team_list),
)

urlpatterns += (
    url(r'^api/workflow/process/positions$', workflow_views.api_workflow_process_positions),
    url(r'^api/workflow/role/action$', workflow_views.api_workflow_role_action),
    url(r'^api/workflow/role/process/actions$', workflow_views.api_workflow_role_process_action),
    url(r'^api/workflow/flow/actions$', workflow_views.api_workflow_flow_actions),
    url(r'^api/workflow/flow/draw$', workflow_views.api_workflow_flow_draw),
    url(r'^api/workflow/role/allcation$', workflow_views.api_workflow_role_allcation),
    url(r'^api/workflow/doc/list$', workflow_views.api_workflow_doc_list),
    url(r'^api/workflow/role/list$', workflow_views.api_workflow_role_list),
    url(r'^api/workflow/node/list$', workflow_views.api_workflow_node_list),
    url(r'^api/workflow/role/image/list$', workflow_views.api_workflow_role_image_list),
    url(r'^api/workflow/flow/copy$', workflow_views.api_workflow_flow_copy),
    url(r'^api/workflow/roles/position/setup$', workflow_views.api_workflow_roles_position_setup),
    url(r'^api/workflow/roles/position$', workflow_views.api_workflow_roles_position),
    url(r'^api/workflow/roles/action$', workflow_views.api_workflow_roles_action),
    url(r'^api/workflow/roles/process/action$', workflow_views.api_workflow_roles_process_action),
    url(r'^api/workflow/roles/allocate$', workflow_views.api_workflow_roles_allocate),
    url(r'^api/workflow/roles/update$', workflow_views.api_workflow_roles_update),
    url(r'^api/workflow/roles/delete$', workflow_views.api_workflow_roles_delete),
    url(r'^api/workflow/docs/update$', workflow_views.api_workflow_docs_update),
    url(r'^api/workflow/docs/delete$', workflow_views.api_workflow_docs_delete),
    url(r'^api/workflow/roles/create$', workflow_views.api_workflow_roles_create),
    url(r'^api/workflow/docs/create$', workflow_views.api_workflow_docs_create),
    url(r'^api/workflow/nodes/update$', workflow_views.api_workflow_nodes_update),
    url(r'^api/workflow/processes$', workflow_views.api_workflow_processes),
    url(r'^api/workflow/detail$', workflow_views.api_workflow_detail),
    url(r'^api/workflow/publish$', workflow_views.api_workflow_publish),
    url(r'^api/workflow/delete$', workflow_views.api_workflow_delete),
    url(r'^api/workflow/update$', workflow_views.api_workflow_update),
    url(r'^api/workflow/create$', workflow_views.api_workflow_create),
    url(r'^api/workflow/list$', workflow_views.api_workflow_list),
    url(r'^api/workflow/related$', workflow_views.api_workflow_related),
    url(r'^api/workflow/role/assign/info$', workflow_views.api_workflow_role_assign_info),
    url(r'^api/workflow/trans/query$', workflow_views.api_workflow_trans_query),
    url(r'^api/workflow/opt/import$', workflow_views.api_workflow_opt_import),
    url(r'^api/workflow/opt/export$', workflow_views.workflow_opt_export),
    url(r'^api/workflow/protected$', workflow_views.api_workflow_protected),
    url(r'^api/workflow/public$', workflow_views.api_workflow_public),
    url(r'^api/workflow/unpublic$', workflow_views.api_workflow_unpublic),
    url(r'^api/workflow/share$', workflow_views.api_workflow_share),
    url(r'^api/workflow/unshare$', workflow_views.api_workflow_unshare),
)

urlpatterns += (
    url(r'^api/group/list$', group_views.get_groups_list),
    url(r'^api/group/create$', group_views.create_new_group),
    url(r'^api/group/delete$', group_views.delete_selected_group),
    url(r'^api/group/update$', group_views.update_group),
    url(r'^api/group/addManager$', group_views.group_add_manager),
    url(r'^api/group/updateManager$', group_views.group_update_manager),
    url(r'^api/group/resetManager$', group_views.group_reset_manager),
    url(r'^api/group/getOwnGroup$', group_views.get_own_group),
    url(r'^api/group/getInstructorItemList$', group_views.get_instructor_items),
    url(r'^api/group/saveInstructors$', group_views.set_instructors),
    url(r'^api/group/createInstructors$', group_views.create_instructors),
    url(r'^api/group/fetchCompanyList$', group_views.get_company_list),
)

urlpatterns += (
    url(r'^api/$', api_views.index),
    url(r'^api/docs/$', api_views.docs),
    url(r'^api/docs/(?P<json>\w+)/$', api_views.module),
)

if settings.DEBUG:
    from django.conf.urls.static import static

    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
