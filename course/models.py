#!/usr/bin/python
# -*- coding=utf-8 -*-

from django.db import models
from account.models import Tuser


# 课堂
# teacher1,teacher2和CourseClass的这种关联设计，很多地方真是不好处理， 真是活久见~~
# 我读大一的时候就知道这样设计是不靠谱的， 当然， 这并没有什么错 - 我现在也懒得改了， 问题并不尖锐的时候先放着
class CourseClass(models.Model):
    no = models.CharField(max_length=16, verbose_name=u'课程号')
    name = models.CharField(max_length=48, verbose_name=u'名称')
    time = models.IntegerField(verbose_name=u'课时')
    experiment_time = models.IntegerField(verbose_name=u'实验学时', null=True)
    sort = models.IntegerField(verbose_name=u'课序号')
    teacher1 = models.ForeignKey(Tuser, blank=True, null=True, related_name='teacher1', verbose_name=u'教师号1')
    teacher2 = models.ForeignKey(Tuser, blank=True, null=True, related_name='teacher2', verbose_name=u'教师号2')
    term = models.CharField(max_length=24, verbose_name=u'开课日期')
    create_time = models.DateTimeField(auto_now_add=True, verbose_name=u'创建时间')
    update_time = models.DateTimeField(auto_now=True, verbose_name=u'修改时间')
    del_flag = models.IntegerField(default=0, choices=((1, u"是"), (0, u"否")), verbose_name=u'是否删除')
    is_share = models.IntegerField(default=0, choices=((1, u"是"), (0, u"否")), verbose_name=u'是否共享')

    class Meta:
        db_table = "t_course_class"
        verbose_name_plural = verbose_name = u"课堂"

    def __unicode__(self):
        return self.name


# 课程
class Course(models.Model):
    name = models.CharField(max_length=48, verbose_name=u'名称')

    class Meta:
        db_table = "t_course"
        verbose_name_plural = verbose_name = u"课程"

    def __unicode__(self):
        return self.name


# 课堂和学生的关联关系, 三期引入
class CourseClassStudent(models.Model):
    # TODO 这个表新创建的，要初始化数据， 初始化数据的脚本如下
    """
        insert into t_course_class_student(course_class_id, student_id)
        SELECT a_id, e_id from (
        SELECT a.id a_id, e.id e_id, a.no c_no, a.name c_name, a.sort c_sort, a.term c_term, b.name t_name, b.username t_username,
                                    a.time c_time, a.experiment_time c_experiment_time, e.username s_username, e.name s_name,
                                    f.name class_name
                        from t_course_class a
                        LEFT JOIN t_user b on a.teacher1_id = b.id
                        LEFT JOIN t_experiment c on a.id = c.course_class_id
                        LEFT JOIN t_member_role d on c.id = d.experiment_id
                        LEFT JOIN t_user e on d.user_id = e.id
                        LEFT JOIN t_class f on e.tclass_id = f.id
                                        where e.id is not null
        ) ttt
    """
    course_class = models.ForeignKey(CourseClass, blank=False, null=False, verbose_name=u'课堂')
    student = models.ForeignKey(Tuser, blank=False, null=False, verbose_name=u'学生')

    class Meta:
        db_table = "t_course_class_student"
        verbose_name_plural = verbose_name = u"课堂学生关联"

    def __unicode__(self):
        return self.course_class.name

