# coding:utf-8
import re
import os, time, random
import datetime
import types
import math
import socket


def check_identity_no(id):
    id = id.upper()
    # 身份证验证
    c = 0
    for (d, p) in zip(map(int, id[:~0]), range(17, 0, -1)):
        c += d * (2 ** p) % 11
    return id[~0] == '10X98765432'[c % 11]


# 验证账号格式
def is_mobile(mobile):
    if mobile:
        if len(mobile) == 11 and re.match("^(1[34587]\d{9})$", mobile) != None:
            return True
        else:
            return False
    else:
        return False


# 判断是否为整数
def IsNumber(varObj):
    if varObj:
        if re.match("^([0-9]*)$", varObj) != None:
            return True
        else:
            return False
    else:
        return False


def IsPrice(varObj):
    if varObj:
        if re.match("^([1-9]\d{0,9}|0)([.]?|(\.\d{1,2})?)$", varObj) != None:
            return True
        else:
            return False
    else:
        return False


def is_qq(qq):
    if qq:
        if re.match("^([1-9][0-9]{4,})$", qq) != None:
            return True
        else:
            return False
    else:
        return False


# 判断是否为字符串 string
def IsString(varObj):
    return type(varObj) is types.StringType


# 判断是否为浮点数 1.324
def IsFloat(varObj):
    return type(varObj) is types.FloatType


# 判断是否为字典 {'a1':'1','a2':'2'}
def IsDict(varObj):
    return type(varObj) is types.DictType


# 判断是否为tuple [1,2,3]
def IsTuple(varObj):
    return type(varObj) is types.TupleType


# 判断是否为List [1,3,4]
def IsList(varObj):
    return type(varObj) is types.ListType


# 判断是否为布尔值 True
def IsBoolean(varObj):
    return type(varObj) is types.BooleanType


# 判断是否为货币型 1.32
def IsCurrency(varObj):
    # 数字是否为整数或浮点数
    if IsFloat(varObj) and IsNumber(varObj):
        # 数字不能为负数
        if varObj > 0:
            return True
    return False


# 判断某个变量是否为空 x
def IsEmpty(varObj):
    if len(varObj) == 0:
        return True
    return False


# 判断变量是否为None None
def IsNone(varObj):
    return type(varObj) is types.NoneType


# 判断是否为日期格式,并且是否符合日历规则 2010-01-31
def IsDate(varObj):
    if len(varObj) == 10:
        rule = '(([0-9]{3}[1-9]|[0-9]{2}[1-9][0-9]{1}|[0-9]{1}[1-9][0-9]{2}|[1-9][0-9]{3})-(((0[13578]|1[02])-(0[1-9]|[12][0-9]|3[01]))|((0[469]|11)-(0[1-9]|[12][0-9]|30))|(02-(0[1-9]|[1][0-9]|2[0-8]))))|((([0-9]{2})(0[48]|[2468][048]|[13579][26])|((0[48]|[2468][048]|[3579][26])00))-02-29)$/'
        match = re.match(rule, varObj)
        if match:
            return True
        return False
    return False


# 判断是否为邮件地址
def IsEmail(varObj):
    rule = '[\w-]+(\.[\w-]+)*@[\w-]+(\.[\w-]+)+$'
    match = re.match(rule, varObj)
    if match:
        return True
    return False


# 判断是否为中文字符串
def IsChineseCharString(varObj):
    for x in varObj:
        if (x >= u"\u4e00" and x <= u"\u9fa5") or (x >= u'\u0041' and x <= u'\u005a') or (
                        x >= u'\u0061' and x <= u'\u007a'):
            continue
        else:
            return False
    return True


# 判断是否为中文字符
def IsChineseChar(varObj):
    if varObj[0] > chr(127):
        return True
    return False


# 判断帐号是否合法 字母开头，允许4-16字节，允许字母数字下划线
def IsLegalAccounts(varObj):
    rule = '[a-zA-Z][a-zA-Z0-9_]{3,15}$'
    match = re.match(rule, varObj)

    if match:
        return True
    return False


# 匹配IP地址
def IsIpAddr(varObj):
    rule = '\d+\.\d+\.\d+\.\d+'
    match = re.match(rule, varObj)

    if match:
        return True
    return False

# 清楚空格
def clear_str_space(s):
    s = s.replace(' ', '')
    s = s.replace(u'　', '')
    return s


def generate_code(length):
    num = '0123456789'
    return ''.join(random.sample(num, length))


def generate_captcha(length):
    return [generate_code(length)]


def random_int_len(start, end, length):
    nums = range(start, end)
    data = random.sample(nums, length)
    return data


def makename(name):
    # 文件扩展名
    ext = os.path.splitext(name)[1]

    # 定义文件名，年月日时分秒随机数
    fn = time.strftime('%Y%m%d%H%M%S')
    fn += '_%d' % random.randint(1, 10000)
    # 重写合成文件名
    name = fn + ext
    return name


def getno():
    t = int(time.time())
    r = random.randint(10, 99)
    s = datetime.datetime.now().microsecond / 1000
    no = str(t) + str(s) + str(r)
    return no


def distance(lat1, lng1, lat2, lng2):
    if lat1 and lng1 and lat2 and lng2:
        R = 6378137
        radLat1 = math.radians(lat1)
        radLng1 = math.radians(lng1)
        radLat2 = math.radians(lat2)
        radLng2 = math.radians(lng2)

        s = math.acos(
            math.cos(radLat1) * math.cos(radLat2) * math.cos(radLng1 - radLng2) + math.sin(radLat1) * math.sin(
                radLat2)) * R
        s = round(s * 10000) / 10000
        return round(s)
    else:
        return 0


def the_months(dt):
    # 本月初
    month = dt.month
    year = dt.year
    day = 1
    return dt.replace(year=year, month=month, day=day)


def last_months(dt, m=1):
    # 上月初
    month = dt.month - m
    if month == 0:
        month = 12
    if month < 0:
        year = dt.year - ((abs(month) + 12) / 12)
        month += 12
    else:
        year = dt.year - month / 12
    day = 1
    return dt.replace(year=year, month=month, day=day)


def next_months(dt, m=1):
    # 下月初
    month = dt.month - 1 + m
    year = dt.year + month / 12
    month = month % 12 + 1
    day = 1
    return dt.replace(year=year, month=month, day=day)


def last_year(dt):
    # 明年初
    year = dt.year - 1
    month = 1
    day = 1
    return dt.replace(year=year, month=month, day=day)


def next_year(dt):
    # 明年初
    year = dt.year + 1
    month = 1
    day = 1
    return dt.replace(year=year, month=month, day=day)


def the_year(dt):
    # 年初
    year = dt.year
    month = 1
    day = 1
    return dt.replace(year=year, month=month, day=day)


def begin_time(dt):
    return dt.replace(minute=0, second=0)


def divmodA(a, b):
    tmp1, tmp2 = divmod(a, b)
    if tmp2 > 0:
        return tmp1 + 1
    else:
        return tmp1


format_date = "%Y-%m-%d"
format_datetime = "%Y-%m-%d %H:%M:%S"


def getCurrentDate():
    """
            获取当前日期：2013-09-10这样的日期字符串
    """
    return time.strftime(format_date, time.localtime(time.time()))


def getCurrentDateTime():
    """
            获取当前时间：2013-09-10 11:22:11这样的时间年月日时分秒字符串
    """
    return time.strftime(format_datetime, time.localtime(time.time()))


def getCurrentHour():
    """
            获取当前时间的小时数，比如如果当前是下午16时，则返回16
    """
    currentDateTime = getCurrentDateTime()
    return currentDateTime[-8:-6]


def getDateElements(sdate):
    """
            输入日期字符串，返回一个结构体组，包含了日期各个分量
            输入：2013-09-10或者2013-09-10 22:11:22
            返回：time.struct_time(tm_year=2013, tm_mon=4, tm_mday=1, tm_hour=21, tm_min=22, tm_sec=33, tm_wday=0, tm_yday=91, tm_isdst=-1)
    """
    dformat = ""
    if judgeDateFormat(sdate) == 0:
        return None
    elif judgeDateFormat(sdate) == 1:
        dformat = format_date
    elif judgeDateFormat(sdate) == 2:
        dformat = format_datetime
    sdate = time.strptime(sdate, dformat)
    return sdate


def getDateToNumber(date1):
    """
            将日期字符串中的减号冒号去掉:
            输入：2013-04-05，返回20130405
            输入：2013-04-05 22:11:23，返回20130405221123
    """
    return date1.replace("-", "").replace(":", "").replace("", "")


def judgeDateFormat(datestr):
    """
            判断日期的格式，如果是"%Y-%m-%d"格式则返回1，如果是"%Y-%m-%d %H:%M:%S"则返回2，否则返回0
            参数 datestr:日期字符串
    """
    try:
        datetime.datetime.strptime(datestr, format_date)
        return 1
    except:
        pass

    try:
        datetime.datetime.strptime(datestr, format_datetime)
        return 2
    except:
        pass

    return 0


def minusTwoDate(date1, date2):
    """
            将两个日期相减，获取相减后的datetime.timedelta对象
            对结果可以直接访问其属性days、seconds、microseconds
    """
    if judgeDateFormat(date1) == 0 or judgeDateFormat(date2) == 0:
        return None
    d1Elements = getDateElements(date1)
    d2Elements = getDateElements(date2)
    if not d1Elements or not d2Elements:
        return None
    d1 = datetime.datetime(d1Elements.tm_year, d1Elements.tm_mon, d1Elements.tm_mday, d1Elements.tm_hour,
                           d1Elements.tm_min, d1Elements.tm_sec)
    d2 = datetime.datetime(d2Elements.tm_year, d2Elements.tm_mon, d2Elements.tm_mday, d2Elements.tm_hour,
                           d2Elements.tm_min, d2Elements.tm_sec)
    return d1 - d2


def dateAddInDays(date1, addcount):
    """
            日期加上或者减去一个数字，返回一个新的日期
            参数date1：要计算的日期
            参数addcount：要增加或者减去的数字，可以为1、2、3、-1、-2、-3，负数表示相减
    """
    try:
        addtime = datetime.timedelta(days=int(addcount))
        d1Elements = getDateElements(date1)
        d1 = datetime.datetime(d1Elements.tm_year, d1Elements.tm_mon, d1Elements.tm_mday)
        datenew = d1 + addtime
        return datenew.strftime(format_date)
    except Exception as e:
        print e
        return None


def is_leap_year(pyear):
    """
            判断输入的年份是否是闰年
    """
    try:
        datetime.datetime(pyear, 2, 29)
        return True
    except ValueError:
        return False


def dateDiffInDays(date1, date2):
    """
            获取两个日期相差的天数，如果date1大于date2，返回正数，否则返回负数
    """
    minusObj = minusTwoDate(date1, date2)
    try:
        return minusObj.days
    except:
        return None


def dateDiffInSeconds(date1, date2):
    """
            获取两个日期相差的秒数
    """
    minusObj = minusTwoDate(date1, date2)
    try:
        return minusObj.days * 24 * 3600 + minusObj.seconds
    except:
        return None


def getWeekOfDate(pdate):
    """
            获取日期对应的周，输入一个日期，返回一个周数字，范围是0~6、其中0代表周日
    """
    pdateElements = getDateElements(pdate)

    weekday = int(pdateElements.tm_wday) + 1
    if weekday == 7:
        weekday = 0
    return weekday


def get_host_ip():
    """
            获取当前IP地址
    """
    myname = socket.getfqdn(socket.gethostname())
    myaddr = socket.gethostbyname(myname)
    # ip = myaddr + ":8080"
    return myaddr


def get_full_sever_address():
    """
        获取服务器完url path地址
    """
    return "http://"+get_host_ip()


def get_expires(m):
    expires = datetime.datetime.now() + datetime.timedelta(minutes=m)
    timestamp = str(int(time.mktime(expires.timetuple()))) + '000'
    return timestamp


def mask_words(words, content):
    """
    功能说明：   替换敏感词
    """
    try:
        if words:
            lst = words.split(',')
            for w in lst:
                content = content.replace(w, '**')
    except Exception as e:
        pass
    return content


def delete_words(words, content):
    """
    功能说明：   替换敏感词
    """
    try:
        if words:
            lst = words.split(',')
            for w in lst:
                content = content.replace(w, '')
        content = content.replace('**', '')
    except Exception as e:
        pass
    return content


def remove_html_tag(html):
    """
    功能说明：   去除html标签
    """
    reg = re.compile('<[^>]*>')
    return reg.sub('', html)


def parse_range(str):
    min = None
    max = None
    try:
        t = str.split('-')
        if len(t) == 2:
            min = int(t[0])
            max = int(t[1])
    except Exception as e:
        print str(e)
    return min, max


def filter_invalid_str(text):
    """
    过滤非BMP字符
    """
    try:
        # UCS-4
        highpoints = re.compile(u'[\U00010000-\U0010ffff]')
    except re.error:
        # UCS-2
        highpoints = re.compile(u'[\uD800-\uDBFF][\uDC00-\uDFFF]')
    return highpoints.sub(u'', text)


def make_key(key, key_prefix, version):
    return ':'.join([key, str(key_prefix), str(version)])


img_ext = ['jpg', 'png', 'bmp', 'gif', 'jpeg']
doc_ext = ['docx']
video_ext = ['mp4', 'avi']
audio_ext = ['mp3', 'amr']


def check_file_type(file):
    ext = file.split(".")[-1]
    ext = ext.lower()
    if ext in doc_ext:
        return 1
    elif ext in img_ext:
        return 2
    elif ext in video_ext:
        return 3
    elif ext in audio_ext:
        return 4
    return 0

# if __name__ == "__main__":
#     print judgeDateFormat("2013-04-01")
#     print judgeDateFormat("2013-04-01 21:22:33")
#     print judgeDateFormat("2013-04-31 21:22:33")
#     print judgeDateFormat("2013-xx")
#     print "--"
#     print datetime.datetime.strptime("2013-04-01", "%Y-%m-%d")
#     print 'elements'
#     print getDateElements("2013-04-01 21:22:33")
#     print 'minus'
#     print minusTwoDate("2013-03-05", "2012-03-07").days
#     print dateDiffInSeconds("2013-03-07 12:22:00", "2013-03-07 10:22:00")
#     print type(getCurrentDate())
#     print getCurrentDateTime()
#     print dateDiffInSeconds(getCurrentDateTime(), "2013-06-17 14:00:00")
#     print getCurrentHour()
#     print dateAddInDays("2013-04-05", -5)
#     print getDateToNumber("2013-04-05")
#     print getDateToNumber("2013-04-05 22:11:33")
#
#     print getWeekOfDate("2013-10-01")
