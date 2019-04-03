# -*- coding: utf-8 -*-
import xlwt as xlwt
from django.db import connection
from decimal import Decimal
from io import BytesIO


def select(sql, columns):
    if sql is None or sql == "":
        return
    try:
        cursor = connection.cursor()
        cursor.execute(sql)
        fetchall = cursor.fetchall()
        object_lis = []
        if fetchall:
            for obj in fetchall:
                row = {}
                for index, c in enumerate(columns):
                    row[c] = obj[index]
                object_lis.append(row)
        return object_lis

    except Exception, e:
        print e
        print sql
        print columns
        return []


def pagination_page(sql, columns, count_sql, page_no, page_num):
    """
    功能说明:     分页处理（获取当前页数据,和页面属性）
    ======================================================
    sql         —— 所有数据 sql 语句
    columns     —— 页面数据属性名,与 sql 的查询结果一一对应
    count_sql   —— 数据总数 sql 语句/也可以传数字
    page_no     —— 页码
    page_num    —— 每页数据量
    =======================================================
    返回数据:
    =======================================================
    {
        "list":[],        —— 页面数据
        "page_attr":[1,65,""]   ——页面属性[页码,总页数,url]
    }
    =======================================================
    """
    if sql is None or sql == "":
        return None
    try:
        cursor = connection.cursor()
        if isinstance(count_sql, int):
            count = count_sql
        else:
            cursor.execute(count_sql)
            count = cursor.fetchall()[0][0]     # 数据总数
        bc = count % page_num
        if bc == 0:
            pages = count/page_num
        else:
            pages = (count/page_num)+1 if bc < page_num else 0    # 总页数
        # 页面数据
        sql += """ limit %s,%s""" % ((int(page_no)-1)*page_num, page_num)
        cursor.execute(sql)
        fetchall = cursor.fetchall()
        object_lis = []        # 页面数据
        if fetchall:
            for obj in fetchall:
                row = {}
                for index, c in enumerate(columns):
                    row[c] = obj[index]
                object_lis.append(row)
        has_previous = False
        has_next = False
        if page_no < pages:
            has_next = True
        if page_no > 1:
            has_previous = True
        paging = {
            'count': count,
            'has_previous': has_previous,
            'has_next': has_next,
            'num_pages': pages,
            'cur_page': page_no,
            'page_size': page_num
        }
        return {'results': object_lis, 'paging': paging}

    except Exception, e:
        print e
        print sql
        print columns
        return {}


def pagination_start(sql, columns, count_sql, start, length, paging=True):
    """
    功能说明:     分页处理（获取当前页数据,和页面属性）
    ======================================================
    sql         —— 所有数据 sql 语句
    columns     —— 页面数据属性名,与 sql 的查询结果一一对应
    count_sql   —— 数据总数 sql 语句/也可以传数字
    start     —— 起始记录
    length    —— 数据长度
    paging --是否分页查询
    =======================================================
    返回数据:
    =======================================================
    {
        "list":[],        —— 页面数据
    }
    =======================================================
    """
    if sql is None or sql == "":
        return None
    try:
        cursor = connection.cursor()

        if isinstance(count_sql, int):
            count = count_sql
        else:
            cursor.execute(count_sql)
            count = cursor.fetchall()[0][0]     # 数据总数

        if paging:
            bc = count % length
            if bc == 0:
                pages = count/length
            else:
                pages = (count/length)+1 if bc < length else 0    # 总页数

            # 页面数据
            sql += """ limit %s,%s""" % (start, length)
        else:
            pages = 1

        cursor.execute(sql)
        fetchall = cursor.fetchall()
        object_lis = []        # 页面数据
        if fetchall:
            for obj in fetchall:
                row = {}
                for index, c in enumerate(columns):
                    if isinstance(obj[index], Decimal):
                        row[c] = str(obj[index])
                    else:
                        row[c] = obj[index]
                object_lis.append(row)

        return {'list': object_lis, 'start': start, 'pages': pages, 'row_size': count}

    except Exception, e:
        print e
        print sql
        print columns
        return {}


def query_sql(sql, columns):
    """
    功能说明:     获取sql数据
    ======================================================
    sql         —— 所有数据 sql 语句
    columns     —— 页面数据属性名,与 sql 的查询结果一一对应
    =======================================================
    返回数据:
    =======================================================
    {
        "list":[],        —— 页面数据
    }
    =======================================================
    """
    if sql is None or sql == "":
        return None
    try:
        cursor = connection.cursor()
        cursor.execute(sql)
        fetchall = cursor.fetchall()
        object_lis = []        # 页面数据
        if fetchall:
            for obj in fetchall:
                row = {}
                for index, c in enumerate(columns):
                    if isinstance(obj[index], Decimal):
                        row[c] = str(obj[index])
                    else:
                        row[c] = obj[index]
                object_lis.append(row)
        return object_lis
    except Exception, e:
        print e
        print sql
        print columns
        return {}


def export_exl(sql, columns, sheet_name):
    """
    生成exl缓存文件
    :param sql: 查询语句
    :param columns: 需要显示的列，可用中文
    :param sheet_name: sheet页名称
    :return: 缓存数据

    =======================================================
    外部返回方法：
    response = StreamingHttpResponse(FileWrapper(cache))
    response['Content-Type'] = 'application/vnd.ms-excel'
    response['Content-Disposition'] = 'attachment;filename="{0}"'.format("test.xls")
    return response
    """
    if sql is None or sql == "":
        return None
    try:
        cursor = connection.cursor()
        cursor.execute(sql)
        fetchall = cursor.fetchall()
        object_lis = []  # 页面数据
        if fetchall:
            for obj in fetchall:
                row = {}
                for index, c in enumerate(columns):
                    if isinstance(obj[index], Decimal):
                        row[c] = str(obj[index])
                    else:
                        row[c] = obj[index]
                object_lis.append(row)
        # 生成exl
        excel = xlwt.Workbook(encoding='utf-8')
        table = excel.add_sheet(sheet_name)

        # 生成标题
        for i in range(len(columns)):
            table.write(0, i, columns[i])

        row = 1
        # 写入数据
        for data in object_lis:
            for index, col in enumerate(columns):
                table.write(row, index, data[col])
            row += 1

        cache = BytesIO()
        excel.save(cache)
        cache.seek(0, 0)
        return cache

    except Exception as e:
        print(e)
        return None
