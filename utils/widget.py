#!/usr/bin/python
# -*- coding=utf-8 -*-
from django.forms.widgets import ClearableFileInput
from django.utils.safestring import mark_safe


class PhotoWidget(ClearableFileInput):
    def render(self, name, value, attrs=None):
        output = super(PhotoWidget, self).render(name, value, attrs)
        if value:
            output += '<div class="row"><div class="col-sm-6 col-md-3">' \
                      '<a href="/media/%s" class="thumbnail" target="_blank">' \
                      '<img src="/media/%s" style="height:200px;width:200px;"/>' \
                      '</a></div></div>' % (value, value)
        return mark_safe(output)

