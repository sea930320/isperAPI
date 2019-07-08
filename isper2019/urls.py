# !/usr/bin/python
# -*- coding=utf-8 -*-

from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin

from account import views as account_views
from cms import views as cms_views
from api import views as api_views
from course import views as course_views
from project import views as project_views
from system import views as system_views
from workflow import views as workflow_views
from group import views as group_views
from dictionary import views as dictionary_views
from userManage import views as userManage_views
from advertising import views as advertising_views
from business import views as business_views
from partPosition import views as partPosition_views
from socketio import views as socketIO_views

urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
]

urlpatterns += (
    url(r'^api/account/query$', account_views.api_account_query),
    url(r'^api/account/users/$', account_views.api_account_users),
    url(r'^api/account/logout$', account_views.api_account_logout),
    url(r'^api/account/login$', account_views.api_account_login), #Jonas
    url(r'^api/account/roles', account_views.api_account_roles), #Jonas
    url(r'^api/account/set/roles/actions', account_views.api_set_roles_actions), #Jonas
    url(r'^api/account/permission', account_views.api_account_permission), #Jonas
    url(r'^api/account/send/code', account_views.api_account_send_verify_code), #Jonas
    url(r'^api/account/users/v3/$', account_views.api_account_users_v3),
    url(r'^api/account/companys/$', account_views.api_account_companys),
    url(r'^api/account/classes/$', account_views.api_account_classes),
    url(r'^api/account/user/update$', account_views.api_account_user_update),
    url(r'^api/account/password/update$', account_views.api_account_password_update),
    url(r'^api/account/avatar-img/update', account_views.api_account_avatar_img_update),
    url(r'^api/account/avatar-img/upload', account_views.api_account_avatar_img_upload),
    url(r'^api/account/user/save$', account_views.api_account_user_save),
    url(r'^api/account/user/create', account_views.api_account_user_create), #Jonas
    url(r'^api/account/get/user/$', account_views.api_account_get_user),
    url(r'^api/account/import$', account_views.api_account_import),
    url(r'^api/account/export$', account_views.api_account_export),
    url(r'^api/account/user/auth/update', account_views.api_account_user_auth_update),
    url(r'^api/account/user/delete', account_views.api_course_user_delete),
    url(r'^api/account/share', account_views.api_account_share), #Jonas
    url(r'^api/account/default-group', account_views.api_get_default_group), #Jonas
    url(r'^api/account/get/loginlogs', account_views.api_get_loginlog_list), #Jonas
    url(r'^api/account/remove/loginlogs', account_views.api_remove_loginlogs), #Jonas
    url(r'^api/account/export/loginlogs', account_views.api_export_loginlogs), #Jonas
    url(r'^api/account/get/worklogs', account_views.api_get_worklog_list), #Jonas
    url(r'^api/account/remove/worklogs', account_views.api_remove_worklogs), #Jonas
    url(r'^api/account/export/worklogs', account_views.api_export_worklogs), #Jonas
    url(r'^api/account/get/assistants', account_views.api_get_assistants), #Jonas
    url(r'^api/account/set/assistants', account_views.api_set_assistants), #Jonas worklog added
    url(r'^api/account/unset/assistant', account_views.api_unset_assistant), #Jonas worklog added
    url(r'^api/account/get/permissions', account_views.api_get_permissions), #Jonas
    url(r'^api/account/set/assistant/actions', account_views.api_set_assistants_actions), #Jonas
    url(r'^api/account/get/getMessageData', account_views.get_own_messages),
    url(r'^api/account/get/worklog-statistic', account_views.api_get_worklog_statistic), #Jonas
    url(r'^api/account/get/user-statistic', account_views.api_get_user_statistic), #Jonas
)

urlpatterns += (
    url(r'^api/cms/to/user/list$', cms_views.api_cms_to_user_list),
    url(r'^api/cms/send/msg$', cms_views.api_cms_send_msg),
    url(r'^api/cms/msg/list$', cms_views.api_cms_msg_list),
    url(r'^api/cms/new/msg/num$', cms_views.api_cms_new_msg_num),
    url(r'^api/cms/to/user/list-business$', cms_views.api_cms_to_user_list_business),
    url(r'^api/cms/msg/list-business$', cms_views.api_cms_msg_list_business),
    url(r'^api/cms/send/msg-business$', cms_views.api_cms_send_msg_business),
    url(r'^api/cms/new/msg-business/num$', cms_views.api_cms_new_msg_num_business),
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
    url(r'^api/project/create$', project_views.api_project_create), # Jonas
    url(r'^api/project/detail$', project_views.api_project_detail),
    url(r'^api/project/docs/detail$', project_views.api_project_docs_detail), # Jonas
    url(r'^api/project/docs/allocate$', project_views.api_project_docs_allocate), # Jonas
    url(r'^api/project/docs/delete$', project_views.api_project_docs_delete), # Jonas
    url(r'^api/project/docs/create$', project_views.api_project_docs_create),
    url(r'^api/project/roles/detail$', project_views.api_project_roles_detail), # Jonas
    url(r'^api/project/roles/configurate$', project_views.api_project_roles_configurate), # Jonas
    url(r'^api/project/role/image/update$', project_views.api_project_role_image_update),
    url(r'^api/project/jump/detail$', project_views.api_project_jump_detail),
    url(r'^api/project/jump/setup$', project_views.api_project_jump_setup),
    url(r'^api/project/update$', project_views.api_project_update),
    url(r'^api/project/has_experiment$', project_views.api_project_has_experiment),
    url(r'^api/project/delete$', project_views.api_project_delete),
    url(r'^api/project/copy$', project_views.api_project_copy),
    url(r'^api/project/list$', project_views.api_project_list),
    url(r'^api/project/related$', project_views.api_project_related),
    url(r'^api/project/protected', project_views.api_project_protected),
    url(r'^api/project/share', project_views.api_project_share),
    url(r'^api/project/unshare', project_views.api_project_unshare),
    url(r'^api/project/getAllUsers_AllParts', project_views.get_allusers_allparts),
)

urlpatterns += (
    url(r'^api/file/upload$', system_views.api_file_upload),
    url(r'^api/system/app/version$', system_views.api_file_upload),
)

urlpatterns += (
    url(r'^api/workflow/list$', workflow_views.api_workflow_list), #Jonas
    url(r'^api/workflow/process/positions$', workflow_views.api_workflow_process_positions), #Jonas
    url(r'^api/workflow/role/action$', workflow_views.api_workflow_role_action), #Jonas
    url(r'^api/workflow/role/process/actions$', workflow_views.api_workflow_role_process_action), #Jonas
    url(r'^api/workflow/flow/actions$', workflow_views.api_workflow_flow_actions),
    url(r'^api/workflow/flow/draw$', workflow_views.api_workflow_flow_draw),
    url(r'^api/workflow/role/allcation$', workflow_views.api_workflow_role_allcation), #Jonas
    url(r'^api/workflow/doc/list$', workflow_views.api_workflow_doc_list),
    url(r'^api/workflow/role/list$', workflow_views.api_workflow_role_list),
    url(r'^api/workflow/node/list$', workflow_views.api_workflow_node_list),
    url(r'^api/workflow/role/image/list$', workflow_views.api_workflow_role_image_list),
    url(r'^api/workflow/flow/copy$', workflow_views.api_workflow_flow_copy), #Jonas
    url(r'^api/workflow/roles/create$', workflow_views.api_workflow_roles_create), #Jonas
    url(r'^api/workflow/roles/position/setup$', workflow_views.api_workflow_roles_position_setup),
    url(r'^api/workflow/roles/position$', workflow_views.api_workflow_roles_position),
    url(r'^api/workflow/roles/action$', workflow_views.api_workflow_roles_action), #Jonas
    url(r'^api/workflow/roles/process/action$', workflow_views.api_workflow_roles_process_action),
    url(r'^api/workflow/roles/allocate$', workflow_views.api_workflow_roles_allocate), #Jonas
    url(r'^api/workflow/roles/update$', workflow_views.api_workflow_roles_update), #Jonas
    url(r'^api/workflow/roles/delete$', workflow_views.api_workflow_roles_delete), #Jonas
    url(r'^api/workflow/docs/update$', workflow_views.api_workflow_docs_update),
    url(r'^api/workflow/docs/delete$', workflow_views.api_workflow_docs_delete), #Jonas
    url(r'^api/workflow/docs/create$', workflow_views.api_workflow_docs_create), #Jonas
    url(r'^api/workflow/nodes/update$', workflow_views.api_workflow_nodes_update), #Jonas
    url(r'^api/workflow/processes$', workflow_views.api_workflow_processes),
    url(r'^api/workflow/detail$', workflow_views.api_workflow_detail), #Jonas
    url(r'^api/workflow/publish$', workflow_views.api_workflow_publish), #Jonas worklog added
    url(r'^api/workflow/delete$', workflow_views.api_workflow_delete), #Jonas worklog added
    url(r'^api/workflow/update$', workflow_views.api_workflow_update), #Jonas worklog added
    url(r'^api/workflow/create$', workflow_views.api_workflow_create), #Jonas worklog added
    url(r'^api/workflow/related$', workflow_views.api_workflow_related),
    url(r'^api/workflow/role/assign/info$', workflow_views.api_workflow_role_assign_info),
    url(r'^api/workflow/trans/query$', workflow_views.api_workflow_trans_query),
    url(r'^api/workflow/opt/import$', workflow_views.api_workflow_opt_import),
    url(r'^api/workflow/opt/export$', workflow_views.workflow_opt_export),
    url(r'^api/workflow/protected$', workflow_views.api_workflow_protected), #Jonas
    url(r'^api/workflow/public$', workflow_views.api_workflow_public), #Jonas worklog added
    url(r'^api/workflow/unpublic$', workflow_views.api_workflow_unpublic), #Jonas worklog added
    url(r'^api/workflow/share$', workflow_views.api_workflow_share), #Jonas worklog added
    url(r'^api/workflow/unshare$', workflow_views.api_workflow_unshare), #Jonas worklog added
    url(r'^api/workflow/job_types', workflow_views.api_workflow_job_types), #Jonas
    url(r'^api/workflow/office_items', workflow_views.api_workflow_office_items), #Jonas
    url(r'^api/workflow/job_type/candidate', workflow_views.api_workflow_job_type_candidate), #Jonas
    url(r'^api/workflow/role/allocation/list', workflow_views.api_workflow_role_allocation_list), #Jonas
    url(r'^api/workflow/role/allocation/create$', workflow_views.api_workflow_role_allocation_create), #Jonas
    url(r'^api/workflow/role/allocation/remove', workflow_views.api_workflow_role_allocation_remove), #Jonas
    url(r'^api/workflow/role/allocation/bulk_update', workflow_views.api_workflow_role_allocation_bulk_update), #Jonas
    url(r'^api/workflow/role/allocation/image_update', workflow_views.api_workflow_role_allocation_image_update), #Jonas
)

urlpatterns += (
    url(r'^api/group/list$', group_views.get_groups_list),
    url(r'^api/group/create$', group_views.create_new_group),
    url(r'^api/group/delete$', group_views.delete_selected_group),
    url(r'^api/group/update$', group_views.update_group),
    url(r'^api/group/addManager$', group_views.group_add_manager),
    url(r'^api/group/addAssistant$', group_views.group_add_assistant), #Jonas
    url(r'^api/group/updateManager$', group_views.group_update_manager),
    url(r'^api/group/resetManager$', group_views.group_reset_manager),
    url(r'^api/group/getOwnGroup$', group_views.get_own_group),
    url(r'^api/group/getInstructorItemList$', group_views.get_instructor_items),
    url(r'^api/group/saveInstructors$', group_views.set_instructors),
    url(r'^api/group/createInstructors$', group_views.create_instructors),
    url(r'^api/group/all-list$', group_views.get_groups_all_list), #Jonas
    url(r'^api/group/checkUserGroup$', group_views.check_user_group),
    url(r'^api/group/deleteGroupManager$', group_views.delete_group_manager),
    url(r'^api/group/deleteGroupInstructor$', group_views.delete_group_instructor),
    url(r'^api/group/getCompanyListOfGroup$', group_views.get_companyList_OfGroup),
    url(r'^api/company/fetchCompanyList$', group_views.get_company_list),
    url(r'^api/company/createCompany$', group_views.create_new_company),
    url(r'^api/company/deleteCompany$', group_views.delete_selected_company),
    url(r'^api/company/updateCompany$', group_views.update_company),
    url(r'^api/company/addCManager$', group_views.add_company_manager),
    url(r'^api/company/addCAssistant$', group_views.add_company_assistant), #Jonas
    url(r'^api/company/updateCManager$', group_views.update_company_manager),
    url(r'^api/company/pCResetManager$', group_views.reset_company_manager),
    url(r'^api/company/deleteCompanyManager$', group_views.delete_company_manager),
)

urlpatterns += (
    url(r'^api/dic/getDicData$', dictionary_views.get_dic_data),
    url(r'^api/dic/getOfficeItemData$', dictionary_views.get_officeItem_data),
    url(r'^api/dic/newItemSave$', dictionary_views.new_item_save),
    url(r'^api/dic/editItemSave$', dictionary_views.edit_item_save),
    url(r'^api/dic/deleteItemSave$', dictionary_views.delete_item_save),
)

urlpatterns += (
    url(r'^api/userManager/getNormalUsers$', userManage_views.get_normal_users), # Jonas Updated for assistant set
    url(r'^api/userManager/getManageUsers$', userManage_views.get_manage_users), # Jonas Updated for assistant set
    url(r'^api/userManager/getInstructorUsers$', userManage_views.get_instructor_users),
    url(r'^api/userManager/getStudentUsers$', userManage_views.get_student_users),
    url(r'^api/userManager/getGroupUsers$', userManage_views.get_group_users),
    url(r'^api/userManager/getGroupNonCompanyUsers$', userManage_views.get_group_nonCompanyUsers),
    url(r'^api/userManager/getGroupChangeList$', userManage_views.get_group_changes),
    url(r'^api/userManager/queryCompanyUsers$', userManage_views.get_company_users),
    url(r'^api/userManager/excelDataSave$', userManage_views.create_company_excelUsers),
    url(r'^api/userManager/newUserSet$', userManage_views.create_company_newUser),
    url(r'^api/userManager/deleteUsers$', userManage_views.delete_company_users),
    url(r'^api/userManager/getCompanyNonReviewUsers$', userManage_views.get_group_nonReviewUsers),
    url(r'^api/userManager/getCompanyChangeList$', userManage_views.get_company_changes),
    url(r'^api/userManager/set_Review$', userManage_views.set_is_review),
    url(r'^api/userManager/set_gChange$', userManage_views.set_group_change),
    url(r'^api/userManager/set_cChange$', userManage_views.set_company_change),
    url(r'^api/userManager/resetPass$', userManage_views.reset_user_password),
    url(r'^api/userManager/sampleUserExcel$', userManage_views.download_sample_excel),
)

urlpatterns += (
    url(r'^api/partPosition/getPartPositionData$', partPosition_views.get_part_positions),
    url(r'^api/partPosition/newPPSave$', partPosition_views.new_part_position),
    url(r'^api/partPosition/deletePPSave$', partPosition_views.delete_part_position),
    url(r'^api/partPosition/getPartUsers$', partPosition_views.get_part_users),
    url(r'^api/partPosition/getNonPPUsers$', partPosition_views.get_non_ppUsers),
    url(r'^api/partPosition/setNewPP$', partPosition_views.set_new_pp),
    url(r'^api/partPosition/getInnerPermissions$', partPosition_views.get_inner_permissions),
    url(r'^api/partPosition/setInnerPermissions$', partPosition_views.set_inner_permissions),
)

urlpatterns += (
    url(r'^api/$', api_views.index),
    url(r'^api/docs/$', api_views.docs),
    url(r'^api/docs/(?P<json>\w+)/$', api_views.module),
)

urlpatterns += (
    url(r'^api/advertising/list_home$', advertising_views.api_advertising_list_home),
    url(r'^api/advertising/list$', advertising_views.api_advertising_list),
    url(r'^api/advertising/delete$', advertising_views.api_advertising_delete),
    url(r'^api/advertising/create$', advertising_views.api_advertising_create),
)

urlpatterns += (
    url(r'^api/business/create', business_views.api_business_create),
    url(r'^api/business/remove', business_views.api_business_remove),
    url(r'^api/business/detail', business_views.api_business_detail),
    # url(r'^api/business/start$', business_views.api_business_start),
    url(r'^api/business/list$', business_views.api_business_list),
    url(r'^api/business/messages$', business_views.api_business_messages),
    url(r'^api/business/templates$', business_views.api_business_templates),
    url(r'^api/business/result', business_views.api_business_result),

    url(r'^api/business/node/detail$', business_views.api_business_node_detail),
    url(r'^api/business/node/messages$', business_views.api_business_node_messages),
    url(r'^api/business/node/function$', business_views.api_business_node_function),
    url(r'^api/business/node/role/docs$', business_views.api_business_node_role_docs),

    url(r'^api/business/trans/path$', business_views.api_business_trans_path),

    url(r'^api/business/note/create$', business_views.api_business_note_create),
    url(r'^api/business/note/list$', business_views.api_business_note_list),

    url(r'^api/business/list_nodel$', business_views.api_business_list_nodel),
    url(r'^api/business/list_del$', business_views.api_business_list_del),
    url(r'^api/business/delete$', business_views.api_business_delete),
    url(r'^api/business/recovery$', business_views.api_business_recovery),
    url(r'^api/business/getUnitUserList$', business_views.get_unit_userList),
    url(r'^api/business/getOwnGUsers$', business_views.get_group_userList),
    url(r'^api/business/setNoneUser$', business_views.set_none_user),
    url(r'^api/business/addMoreTeammates$', business_views.add_more_teammates),
    url(r'^api/business/role/status$', business_views.api_business_role_status),
    url(r'^api/business/message/push$', business_views.api_business_message_push),
    url(r'^api/business/message/save', socketIO_views.save_message),
    url(r'^api/business/role/in/list', business_views.api_business_role_in_list),
    url(r'^api/business/role/out/list$', business_views.api_business_role_out_list),
    url(r'^api/business/docs/create$', business_views.api_business_docs_create),
    url(r'^api/business/file/display/list$', business_views.api_business_file_display_list),
    url(r'^api/business/role/report/list$', business_views.api_business_role_schedule_report_list),
    url(r'^api/business/request/sign/roles$', business_views.api_business_request_sign_roles),
    url(r'^api/business/post$', business_views.api_business_post),
    url(r'^api/business/post/create$', business_views.api_business_post_create),
    url(r'^api/business/post/detail', business_views.api_business_post_info),

    url(r'^api/business/report/generate$', business_views.api_business_report_generate),
    url(r'^api/business/report/export', business_views.api_business_report_export),
    url(r'^api/business/experience/list$', business_views.api_business_experience_list),
    url(r'^api/business/experience/save$', business_views.api_business_save_experience),

    url(r'^api/business/templates$', business_views.api_business_templates),

    url(r'^api/business/jump/start', business_views.api_business_jump_start),

    url(r'^api/business/vote/getInitVoteData$', business_views.api_vote_get_init_data),
    url(r'^api/business/vote/saveVoteData$', business_views.api_vote_save_vote_data),
    url(r'^api/business/vote/finishVote$', business_views.api_vote_finish_mode_3),
    url(r'^api/business/vote/userVoteSave$', business_views.api_user_vote_save),
    url(r'^api/business/vote/userVoteItemSave$', business_views.api_user_vote_item_save),

    url(r'^api/business/poll/getInitPollData$', business_views.api_get_poll_init_data),
    url(r'^api/business/poll/savePollData$', business_views.api_save_poll_data),
    url(r'^api/business/poll/userPollSave$', business_views.api_user_poll_save),

    # added by ser for edit module *start
    url(r'^api/business/template/create$', business_views.api_business_template_create),
    url(r'^api/business/template/new$', business_views.api_business_template_new),
    url(r'^api/business/template/sign$', business_views.api_business_template_sign),

    url(r'^api/business/docs/delete$', business_views.api_business_docs_delete),
    url(r'^api/business/step/status$', business_views.api_business_step_status),
    url(r'^api/business/step/status/update$', business_views.api_business_step_status_update),
    url(r'^api/business/doc/team/status$', business_views.api_business_doc_team_status),
    url(r'^api/business/doc/team/status/create$', business_views.api_business_doc_team_status_create),
    url(r'^api/business/doc/team/status/update$', business_views.api_business_doc_team_staus_update)
    # added by ser for edit module *end
)
urlpatterns += (
    url(r'^save_message/$', socketIO_views.save_message, name='socket_io_save_message'),
)
if settings.DEBUG:
    from django.conf.urls.static import static

    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
