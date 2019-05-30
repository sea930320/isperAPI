# -*- coding=utf-8 -*-
from django.contrib import admin

# Register your models here.
#!/usr/bin/python
# -*- coding=utf-8 -*-

from django.contrib import admin
from models import *


class AdvertisingAdmin(admin.ModelAdmin):
    list_advertising = ['flow_id', 'name', 'all_role', 'course', 'reference', 'public_status', 'level', 'entire_graph', 'type', 'can_redo', 'is_open', 'ability_target', 'start_time', 'end_time', 'intro', 'purpose', 'requirement', 'created_by', 'create_time', 'update_time', 'del_flag']

admin.site.register(Advertising, AdvertisingAdmin)
