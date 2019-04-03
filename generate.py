#!/usr/bin/python
# -*- coding=utf-8 -*-

from django.utils.crypto import get_random_string
import os
import re
import shutil
import sys
import urllib
import urllib2
import json
import pickle
import zipfile
import time

try:
    import zlib

    compression = zipfile.ZIP_DEFLATED
except:
    compression = zipfile.ZIP_STORED


class MakeCode:
    def __init__(self, user, pwd, server_path, server_bak_path, prjName, module=None, url=None):
        self.user = user
        self.pwd = pwd

        self.server_path = server_path  # 原目录，工程目录
        self.server_bak_path = server_bak_path
        self.prjName = prjName
        self.prj_path = os.path.join(self.server_path, self.prjName)
        self.prj_bak_path = os.path.join(self.server_bak_path, self.prjName)
        self.module = module
        self.templatesApiPath = os.path.join(self.server_path, "templates", "api")
        self.base_url = url
        self.media = None
        self.user_models = None

    def init_para(self, media):
        self.media = media

    def make_all(self):
        src_path = os.path.join(self.media, 'server_bak')
        self.copy_prj(src_path)
        bFlag, d = self.make()
        if bFlag:
            self.make_prj()
            self.make_settings(self.prjName, d['module'])
            zipfilepath = self.compress()

            try:
                # 删除刚生成的工程目录
                shutil.rmtree(self.server_bak_path)
                pass
            except:
                pass

            return 0, 'ok', zipfilepath
        else:
            return -1, d, ''

    def make_add(self):
        bFlag, d = self.make()
        if bFlag:
            zipfilepath = self.compress()
            return 0, '', zipfilepath
        else:
            return -1, d, ''

    def make(self):
        bFlag, d = self.get_prj_data(self.base_url)
        if bFlag:
            self.make_path()
            self.make_module(d['module'])
            self.make_table(d['table'], d['auto_table'], d['class_module'])
            self.make_api(d['module'], d['api'], d['auto_api'], d['class_module'])
            return True, d
        else:
            return False, d

    def copy_prj(self, src_path):
        if os.path.exists(self.server_bak_path):
            for i in range(0, 2):
                time.sleep(0.1)
                try:
                    shutil.rmtree(self.server_bak_path)
                    break
                except:
                    pass
                    # os.makedirs(self.server_bak_path)

        shutil.copytree(src_path, self.server_bak_path)

    def make_prj(self):
        fh = open(os.path.join(self.server_bak_path, self.prjName, '__init__.py'), "wb")
        fh.write('#!/usr/bin/python\r\n')
        fh.write('# -*- coding=utf-8 -*-\r\n')
        fh.close()

        fh = open(os.path.join(self.server_bak_path, self.prjName, 'wsgi.py'), "wb")
        fh.write('#!/usr/bin/python\r\n')
        fh.write('# -*- coding=utf-8 -*-\r\n')
        fh.write('\r\n')
        fh.write('import os\r\n')
        fh.write('from django.core.wsgi import get_wsgi_application\r\n')
        fh.write('\r\n')
        fh.write('os.environ.setdefault("DJANGO_SETTINGS_MODULE", "%s.settings")\r\n' % self.prjName)
        fh.write('application = get_wsgi_application()\r\n')
        fh.write('\r\n')
        fh.close()

        fh = open(os.path.join(self.server_bak_path, 'manage.py'), "wb")
        fh.write('#!/usr/bin/python\r\n')
        fh.write('# -*- coding=utf-8 -*-\r\n')
        fh.write('\r\n')
        fh.write('import os\r\n')
        fh.write('import sys\r\n')
        fh.write('\r\n')
        fh.write('if __name__ == "__main__":\r\n')
        fh.write('    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "%s.settings")\r\n' % self.prjName)
        fh.write('    from django.core.management import execute_from_command_line\r\n')
        fh.write('    execute_from_command_line(sys.argv)\r\n')
        fh.write('\r\n')
        fh.close()

        fh = open(os.path.join(self.server_bak_path, 'kill.sh'), "wb")
        fh.write("for i in `ps -ef|grep %s.wsgi|grep -v grep|awk '{print $2}'`\n" % self.prjName)
        fh.write("do\n")
        fh.write('kill -9 $i\n')
        fh.write('done\n')
        fh.close()

        fh = open(os.path.join(self.server_bak_path, 'start.sh'), "wb")
        fh.write("gunicorn --config gunicorn.conf %s.wsgi:application --daemon" % self.prjName)
        fh.close()

        fh = open(os.path.join(self.server_bak_path, 'gunicorn.conf'), "wb")
        fh.write("bind = '127.0.0.1:8080'\n")
        fh.write("workers = 1\n")
        fh.write("proc_name = '%s'\n" % self.prjName)
        fh.write("pidfile = '/tmp/%s.pid'\n" % self.prjName)
        fh.close()

    def compress(self):
        zipfilepath = os.path.abspath(os.path.join(self.media, "%s.zip" % self.prjName))
        if os.path.exists(zipfilepath):
            os.remove(zipfilepath)

        z = zipfile.ZipFile(zipfilepath, mode="w", compression=compression)
        startdir = os.path.abspath(os.path.join(self.media, self.prjName))
        # startdir = self.server_bak_path
        for dirpath, dirnames, filenames in os.walk(startdir):
            for filename in filenames:
                tmp_filename = os.path.join(dirpath, filename)
                arcname = tmp_filename.replace(startdir, "")
                z.write(tmp_filename, arcname)
        z.close()

        return zipfilepath

    def get_prj_data(self, base_url):
        if self.media:
            from check import views
            the_page = views._get_generate_data(self.prjName, self.module)

        else:
            if self.module:
                url = r'%s/get_generate_data?user=%s&pwd=%s&prjName=%s&module=%s' % (base_url.rstrip("/"),
                                                                                     self.user, self.pwd, self.prjName,
                                                                                     self.module)
            else:
                url = r'%s/get_generate_data?user=%s&pwd=%s&prjName=%s' % (
                    base_url.rstrip("/"), self.user, self.pwd, self.prjName)

            req = urllib2.Request(url)
            response = urllib2.urlopen(req)
            the_page = response.read()

        dictData = pickle.loads(the_page)

        if dictData['c'] != 0:
            print dictData['e']
            return False, dictData['e']
        else:
            d = dictData['d']

        return True, d

    def make_path(self):
        if not os.path.exists(self.server_path):
            os.makedirs(self.server_path)

        if not os.path.exists(self.server_bak_path):
            os.makedirs(self.server_bak_path)

        if not os.path.exists(self.prj_path):
            os.makedirs(self.prj_path)

        if not os.path.exists(self.prj_bak_path):
            os.makedirs(self.prj_bak_path)

        if not os.path.exists(self.templatesApiPath):
            os.makedirs(self.templatesApiPath)

    def make_api(self, dictModule, dictModule_api, dictAutoApi, dictClassName_moduleName):
        self._makeApi_views(dictModule_api, dictClassName_moduleName, dictAutoApi)
        self._makeApi_url(dictModule, dictModule_api)
        self._makeApi(dictModule, dictModule_api)

    def _makeApi(self, dictModule, dictModule_api):

        lstLine = []
        lstLine.append(u'{')
        lstLine.append(u'    "apiVersion": "1.0.5",')
        lstLine.append(u'    "swaggerVersion": "1.2",')
        lstLine.append(u'    "apis":[')

        for name_en, lstApi in dictModule_api.items():
            dictSigModule = dictModule[name_en]
            name_ch = dictSigModule["name_ch"]

            lstLine.append(u'        {')
            lstLine.append(u'            "path": "/%s",' % name_en)
            lstLine.append(u'            "description":"%s(%s)"' % (name_ch, len(lstApi)))
            lstLine.append(u'        },')

            lstApiLine = []
            lstApiLine.append(u'{')
            lstApiLine.append(u'    "apiVersion": "1.0.5",')
            lstApiLine.append(u'    "swaggerVersion": "1.2",')
            lstApiLine.append(u'    "basePath": "/",')
            lstApiLine.append(u'    "resourcePath": "/%s",' % name_en)
            lstApiLine.append(u'    "produces":[')
            lstApiLine.append(u'        "application/json",')
            lstApiLine.append(u'        "application/xml",')
            lstApiLine.append(u'        "text/plain",')
            lstApiLine.append(u'        "text/html"')
            lstApiLine.append(u'    ],')
            lstApiLine.append(u'')
            lstApiLine.append(u'    "apis":[')

            for oApi in lstApi:
                lstApiLine.append(u'        {')
                lstApiLine.append(u'            "path":"/%s",' % oApi["url"].lstrip("/"))
                lstApiLine.append(u'            "operations":[')
                lstApiLine.append(u'                {')
                if oApi["way"] == u"0":
                    lstApiLine.append(u'                    "method":"POST",')
                else:
                    lstApiLine.append(u'                    "method":"GET",')

                lstApiLine.append(u'                    "summary":"%s",' % oApi["name"])
                lstApiLine.append(u'                    "notes":"",')

                lstApiPara = oApi["api_para"]
                if lstApiPara:
                    lstApiLine.append(
                        u'                    "nickname":"%s_%s",' % (name_en, oApi["url"].replace(u'/', u'_')))
                    lstApiLine.append(u'                    "parameters":[')
                else:
                    lstApiLine.append(
                        u'                    "nickname":"%s_%s"' % (name_en, oApi["url"].replace(u'/', u'_')))

                for oApiPara in lstApiPara:
                    lstApiLine.append(u'                        {')
                    lstApiLine.append(u'                            "name":"%s",' % oApiPara["name"])
                    if oApiPara["default"]:
                        lstApiLine.append(
                            u'                            "description":"%s(默认:%s)",' % (oApiPara["explana"].replace('"', "'"), oApiPara["default"].replace('"', "'")))
                    else:
                        lstApiLine.append(
                            u'                            "description":"%s",' % oApiPara["explana"].replace('"', "'"))

                    if oApiPara["type"] == "0":
                        lstApiLine.append(u'                            "type": "string",')
                    elif oApiPara["type"] == "1":
                        lstApiLine.append(u'                            "type": "integer",')
                    else:
                        lstApiLine.append(u'                            "type": "File",')

                    if oApi["way"] == u"0":  # post
                        lstApiLine.append(u'                            "paramType": "form",')
                    else:
                        lstApiLine.append(u'                            "paramType": "query",')

                    if oApiPara["required"]:
                        lstApiLine.append(u'                            "required": true,')
                    else:
                        lstApiLine.append(u'                            "required": false,')

                    lstApiLine.append(u'                            "allowMultiple": false')
                    lstApiLine.append(u'                        },')

                if lstApiPara:
                    lstApiLine[-1] = u'                        }'
                    lstApiLine.append(u'                    ]')

                lstApiLine.append(u'                }')
                lstApiLine.append(u'            ]')
                lstApiLine.append(u'        },')

            lstApiLine[-1] = u'        }'
            lstApiLine.append(u'    ]')
            lstApiLine.append(u'}')

            fh = open(os.path.join(self.templatesApiPath, '%s.json' % name_en), "wb")
            buf = u'\r\n'.join(lstApiLine)
            fh.write(buf.encode('utf-8'))
            fh.close()

        if lstLine[-1] == u'        },':
            lstLine[-1] = u'        }'
        lstLine.append(u'    ]')
        lstLine.append(u'}')
        lstLine.append(u'')

        fh = open(os.path.join(self.templatesApiPath, 'docs.json'), "wb")
        buf = u'\r\n'.join(lstLine)
        fh.write(buf.encode('utf-8'))
        fh.close()

    def _makeApi_url(self, dictModule, dictModule_api):
        lstLine = []
        lstLine.append(u'#!/usr/bin/python')
        lstLine.append(u'# -*- coding=utf-8 -*-')
        lstLine.append(u'')
        lstLine.append(u'from django.conf.urls import include, url')
        lstLine.append(u'from django.contrib import admin')
        lstLine.append(u'from django.contrib.staticfiles.urls import staticfiles_urlpatterns')
        lstLine.append(u'from django.conf import settings')
        lstLine.append(u'from api import views as api_views')
        lstModuleName = dictModule.keys()
        lstModuleName.sort()
        for name_en in lstModuleName:
            # for (name_en, name_ch), lstApi in dictModule_api.items():
            if not dictModule_api.has_key(name_en):
                continue

            lstLine.append(u'from %s import views as %s_views' % (name_en, name_en))

        lstLine.append(u'')

        lstLine.append(u'urlpatterns = [')
        lstLine.append(u"    url(r'^admin/', include(admin.site.urls)),")
        # lstLine.append(u"    url(r'^ueditor/',include('DjangoUeditor.urls' )),")
        # lstLine.append(u"    url(r'^select2/', include('django_select2.urls')),")
        lstLine.append(u']')

        for name_en in lstModuleName:
            # for (name_en, name_ch), lstApi in dictModule_api.items():
            if not dictModule_api.has_key(name_en):
                continue

            lstApi = dictModule_api[name_en]
            lstLine.append(u"")
            lstLine.append(u"urlpatterns += (")

            for oApi in lstApi:
                funName = oApi["url"].strip(u"/")
                url = funName
                lstPara = re.findall(r'{(.*?)}', funName)
                for sPara in lstPara:
                    funName = funName.replace(u'{%s}' % sPara, u'')
                    url = url.replace(u'{%s}' % sPara, u'(?P<%s>\d+)' % sPara)
                funName = funName.replace(u'/', u'_')
                funName = funName.strip(u"_")

                lstLine.append(u"    url(r'^%s$', %s_views.%s)," % (url, name_en, funName))

            lstLine.append(u')')
            # lstLine.append(u'')

        lstLine.append(u'')
        lstLine.append(u"urlpatterns += (")
        lstLine.append(u"    url(r'^api/$', api_views.index),")
        lstLine.append(u"    url(r'^api/docs/$', api_views.docs),")
        lstLine.append(u"    url(r'^api/docs/(?P<json>\w+)/$', api_views.module),")
        lstLine.append(u")")
        lstLine.append(u"")

        # lstLine.append(u"urlpatterns += staticfiles_urlpatterns()")
        # lstLine.append(u"if settings.DEBUG:")
        # lstLine.append(u"    urlpatterns += patterns('',")
        # lstLine.append(u"                            url(r'^media/(?P<path>.*)$',")
        # lstLine.append(u"                                'django.views.static.serve',")
        # lstLine.append(u"                                {'document_root': settings.MEDIA_ROOT,}),")
        # lstLine.append(u"                            )")
        # lstLine.append(u"")

        fh = open(os.path.join(self.prj_bak_path, 'urls.py'), "wb")
        buf = u'\r\n'.join(lstLine)
        fh.write(buf.encode('utf-8'))
        fh.close()

    def _makeApi_views(self, dictModule_api, dictClassName_moduleName, dictAutoApi):
        lstErrCode = []
        for name_en, lstApi in dictModule_api.items():
            lstLine = []
            lstHead = []

            lstLine.append(u'from django.http import HttpResponse')
            lstLine.append(u'from utils.request_auth import *')
            lstLine.append(u'from utils.err_code import *')
            lstLine.append(u'import json')
            lstLine.append(u'import traceback')
            lstLine.append(u'import logging')

            lstLine.append(u'')
            lstLine.append(u'logger = logging.getLogger(__name__)')
            lstLine.append(u'')
            for oApi in lstApi:
                lstLine.append(u'# %s' % oApi["name"])
                if oApi["explana"] not in ("", None):
                    lstLine.append(u"'''")
                    lstLine.append(oApi.explana)
                    lstLine.append(u"'''")

                # 自动生成
                if oApi["auto_generate"]:
                    oOutoApi = dictAutoApi[oApi["autoId"]]

                    if oOutoApi["content"]:
                        oRe = re.search('\[begin error_code\](.*)\[end error_code\]', oOutoApi["content"], re.I | re.S)
                        if oRe:
                            err_code = oRe.groups()[0].strip()
                            if err_code:
                                lstErr = err_code.split("\r\n")
                                for sErrCode in lstErr:
                                    if sErrCode not in lstErrCode:
                                        lstErrCode.append(sErrCode)

                        oRe = re.search('\[begin head\](.*)\[end head\]', oOutoApi["content"], re.I | re.S)
                        if oRe:
                            head = oRe.groups()[0].strip()
                            if head:
                                lstTmpHead = head.split("\r\n")
                                for sHead in lstTmpHead:
                                    if '{models}' in sHead:
                                        className = re.search("import (.*)", sHead, re.I).groups()[0]
                                        if dictClassName_moduleName[className] != name_en:
                                            sHead = sHead.replace('{models}',
                                                                  "%s.models" % dictClassName_moduleName[className])
                                        else:
                                            sHead = sHead.replace('{models}', "models")

                                    elif '{project}' in sHead:
                                        sHead = sHead.replace('{project}', oApi["prjName"])

                                    if sHead not in lstHead:
                                        lstHead.append(sHead)

                        oRe = re.search('\[begin content\](.*)\[end content\]', oOutoApi["content"], re.I | re.S)
                        if oRe:
                            content = oRe.groups()[0].strip("\r\n")
                            if content.strip():
                                lstLine.append(content)
                                lstLine.append("\r\n\r\n")
                    continue
                    pass

                funName = oApi["url"].strip(u"/")
                funName = funName.strip(u"_")
                lstPara = re.findall(r'{(.*?)}', funName)
                for sPara in lstPara:
                    funName = funName.replace(u'{%s}' % sPara, u'')

                funName = funName.replace(u'/', u'_').strip(u"_")
                if lstPara:
                    lstLine.append(u'def %s(request, %s):' % (
                        funName, str(lstPara).strip(u"[],").replace("u'", '').replace("'", '')))
                else:
                    lstLine.append(u'def %s(request):' % funName)

                if oApi["way"] == "0":
                    lstLine.append(u'    dictResp = auth_check(request, "POST")')
                else:
                    lstLine.append(u'    dictResp = auth_check(request, "GET")')
                lstLine.append(u'    if dictResp != {}:')
                lstLine.append(
                    u'        return HttpResponse(json.dumps(dictResp, ensure_ascii=False), content_type="application/json")')

                lstLine.append(u'')
                lstLine.append(u'    try:')
                lstApiPara = oApi["api_para"]
                if oApi["way"] == "0":  # post
                    for oApiPara in lstApiPara:
                        if oApiPara in lstPara:
                            continue

                        if oApiPara["required"]:
                            if oApiPara["type"] == u"0":  # string类型
                                lstLine.append(
                                    u'        %s = request.POST["%s"]  # %s' % (
                                        oApiPara["name"], oApiPara["name"], oApiPara["explana"]))
                            elif oApiPara["type"] == u"1":  # int类型:
                                lstLine.append(
                                    u'        %s = int(request.POST["%s"])  # %s' % (
                                        oApiPara["name"], oApiPara["name"], oApiPara["explana"]))

                            elif oApiPara["type"] == u"2":  # file类型:
                                lstLine.append(
                                    u'        %s = request.FILES["%s"])  # %s' % (
                                        oApiPara["name"], oApiPara["name"], oApiPara["explana"]))
                        else:
                            if oApiPara["type"] == u"0":  # string类型
                                lstLine.append(u'        %s = request.POST.get("%s", "%s")  # %s' % (
                                    oApiPara["name"], oApiPara["name"], oApiPara["default"], oApiPara["explana"]))
                            elif oApiPara["type"] == u"1":  # int类型:
                                lstLine.append(u'        %s = int(request.POST.get("%s", %s))  # %s' % (
                                    oApiPara["name"], oApiPara["name"], oApiPara["default"], oApiPara["explana"]))
                            elif oApiPara["type"] == u"2":  # file类型:
                                lstLine.append(u'        %s = request.FILES.get("%s", %s)  # %s' % (
                                    oApiPara["name"], oApiPara["name"], oApiPara["default"] or "None", oApiPara["explana"]))
                else:
                    for oApiPara in lstApiPara:
                        if oApiPara in lstPara:
                            continue

                        if oApiPara["required"]:
                            lstLine.append(u'        %s = request.GET["%s"]  # %s' % (
                                oApiPara["name"], oApiPara["name"], oApiPara["explana"]))
                        else:
                            if oApiPara["type"] == u"0":  # string类型
                                lstLine.append(
                                    u'        %s = request.GET.get("%s", "")  # %s' % (
                                        oApiPara["name"], oApiPara["name"], oApiPara["explana"]))
                            else:
                                lstLine.append(
                                    u'        %s = request.GET.get("%s", 0)  # %s' % (
                                        oApiPara["name"], oApiPara["name"], oApiPara["explana"]))

                lstLine.append(u'')
                lstApiResult = oApi["api_reuslt"]
                sTmpResult = ""
                for oApiResult in lstApiResult:
                    if oApiResult["name1"] in ["c", "m", "", None]:
                        continue
                    sTmpResult += ', "%s": []' % oApiResult["name1"].replace("'", "")
                if sTmpResult:
                    lstLine.append(u'        dictResp = {"c": ERR_SUCCESS[0]%s}' % sTmpResult)
                else:
                    lstLine.append(u'        dictResp = {"c": ERR_SUCCESS[0]}')
                lstLine.append(
                    u'        return HttpResponse(json.dumps(dictResp, ensure_ascii=False), content_type="application/json")')
                lstLine.append(u'')
                lstLine.append(u'    except:')
                lstLine.append(u'        sErrInfo = traceback.format_exc()')
                lstLine.append(u'        logger.error(sErrInfo)')
                lstLine.append(u'        dictResp = {"c": -1, "m": sErrInfo}')
                lstLine.append(
                    u'        return HttpResponse(json.dumps(dictResp, ensure_ascii=False), content_type="application/json")')
                lstLine.append(u'')
                lstLine.append(u'')

            for sHead in lstHead:
                lstLine.insert(0, sHead)
            lstLine.insert(0, u'')
            lstLine.insert(0, u'# -*- coding=utf-8 -*-')
            lstLine.insert(0, u'#!/usr/bin/python')

            sTmpPath = os.path.join(self.server_bak_path, name_en)
            if not os.path.exists(sTmpPath):
                os.makedirs(sTmpPath)

            fh = open(os.path.join(sTmpPath, 'views.py'), "wb")
            buf = u'\r\n'.join(lstLine)
            fh.write(buf.encode('utf-8'))
            fh.close()

        sTmpPath = os.path.join(self.server_bak_path, 'utils')
        if not os.path.exists(sTmpPath):
            os.makedirs(sTmpPath)

        fh = open(os.path.join(sTmpPath, 'err_code.py'), "wb")
        lstErrCode.insert(0, u'')
        lstErrCode.insert(0, u'# -*- coding=utf-8 -*-')
        lstErrCode.insert(0, u'#!/usr/bin/python')
        buf = u'\r\n'.join(lstErrCode)
        fh.write(buf.encode('utf-8'))
        fh.close()

    def make_module(self, dictModule):
        for (name_en, dictTmp) in dictModule.items():
            sModulePath = os.path.join(self.server_bak_path, name_en)
            if not os.path.exists(sModulePath):
                os.mkdir(sModulePath)

            fh = open(os.path.join(sModulePath, '__init__.py'), "wb")
            lstLine = [u'#!/usr/bin/python', u'# -*- coding=utf-8 -*-\r\n',
                       u'default_app_config = "%s.apps.AppConfig"\r\n' % name_en]
            buf = u"\r\n".join(lstLine)
            fh.write(buf.encode('utf-8'))
            fh.close()

            fh = open(os.path.join(sModulePath, 'apps.py'), "wb")
            lstLine = [u'#!/usr/bin/python', u'# -*- coding=utf-8 -*-\r\n', u'from django.apps import AppConfig\r\n']
            lstLine.append(u'class AppConfig(AppConfig):')
            lstLine.append(u'    name = "%s"' % name_en)
            lstLine.append(u'    verbose_name = u"%s"' % dictTmp["name_ch"])
            buf = u"\r\n".join(lstLine)
            fh.write(buf.encode('utf-8'))
            fh.close()

    def _check_generate(self, lstClassName, oTab, dictClass_field, lstAllClassName):
        for field in dictClass_field[oTab["className"]]:
            if field.has_key("selectForeignKey_className"):
                if field["selectForeignKey_className"] not in lstAllClassName:
                    pass
                elif field["selectForeignKey_className"] == oTab["className"]:
                    pass
                elif field["selectForeignKey_className"] not in lstClassName:
                    return False

        return True

    def make_table(self, dictModule_table, dictAutoTable, dictClassName_moduleName):
        dictClass_field = {}
        dictModule_className = {}

        for name_en, lstTab in dictModule_table.items():
            for oTab in lstTab:
                for field in oTab["field"]:
                    dictClass_field.setdefault(oTab["className"], []).append(field)
                dictModule_className.setdefault(name_en, []).append(oTab["className"])

        for module, lstTab in dictModule_table.items():
            lstAdmin = []
            lstModels = []
            lstModelsHead = []
            lstAdminHead = []

            iTabLen = len(lstTab)
            lstAllClassName = dictModule_className[module]
            lstClassName = []

            sHead = u'from models import *'
            if sHead not in lstAdminHead:
                lstAdminHead.append(sHead)

            while True:
                if len(lstClassName) == iTabLen:
                    break

                for oTab in lstTab:
                    if oTab["className"] in lstClassName:
                        continue

                    if not self._check_generate(lstClassName, oTab, dictClass_field, lstAllClassName):
                        continue

                    lstClassName.append(oTab["className"])

                    lstSigAdmin = []
                    lstSigModels = []

                    if oTab["is_user"]:
                        self.user_models = u"%s.%s" % (module, oTab["className"])
                        lstModelsHead.append(u'from django.contrib.auth.models import BaseUserManager, AbstractBaseUser, PermissionsMixin')
                        lstSigModels.append(u'class UserManager(BaseUserManager):')
                        lstSigModels.append(u'    def create_user(self, username, password=None, **kwargs):')
                        lstSigModels.append(u'        if (not username) or (not password):')
                        lstSigModels.append(u'            raise ValueError("UserManager create user param error")')
                        lstSigModels.append(u'')
                        lstSigModels.append(u'        user = self.model(username=username)')
                        lstSigModels.append(u'        user.set_password(password)')
                        lstSigModels.append(u'        if kwargs:')
                        lstSigModels.append(u'            if kwargs.get("nickname", None):')
                        lstSigModels.append(u'                user.nickname = kwargs["nickname"]')
                        lstSigModels.append(u'            if kwargs.get("email", None):')
                        lstSigModels.append(u'                user.email = kwargs["email"]')
                        lstSigModels.append(u'            if kwargs.get("phone", None):')
                        lstSigModels.append(u'                user.phone = kwargs["phone"]')
                        lstSigModels.append(u'        user.save(using=self._db)')
                        lstSigModels.append(u'        return user')
                        lstSigModels.append(u'')
                        lstSigModels.append(u'')
                        lstSigModels.append(u'    def create_superuser(self, username, password):')
                        lstSigModels.append(u'        accounts = self.create_user(username=username, password=password)')
                        lstSigModels.append(u'        accounts.is_superuser = True')
                        lstSigModels.append(u'        accounts.is_admin = True')
                        lstSigModels.append(u'        accounts.save(using=self._db)')
                        lstSigModels.append(u'        return accounts')
                        lstSigModels.append(u'')
                        lstSigModels.append(u'')

                        lstSigModels.append(u'# %s' % oTab["explana"])
                        lstSigModels.append(u'class %s(AbstractBaseUser, PermissionsMixin):' % oTab["className"])
                    else:
                        lstSigModels.append(u'# %s' % oTab["explana"])
                        lstSigModels.append(u'class %s(models.Model):' % oTab["className"])

                    lstField = oTab["field"]

                    lstFieldName = []

                    for oField in lstField:
                        sLine = self._makeField(oTab["className"], oField, lstModelsHead, module, dictClassName_moduleName, lstField)
                        lstSigModels.append(sLine)
                        lstFieldName.append(str(oField["name"]))

                    if oTab["is_user"]:
                        lstSigModels.append(u'')
                        lstSigModels.append(u'    objects = UserManager()')
                        lstSigModels.append(u'')
                        lstSigModels.append(u'    USERNAME_FIELD = "username"')
                        lstSigModels.append(u'    REQUIRED_FIELDS = []')

                    lstSigModels.append(u'')
                    lstSigModels.append(u'    class Meta:')
                    lstSigModels.append(u'        db_table = "%s"' % oTab["name"])
                    lstSigModels.append(u'        verbose_name_plural = u"%s"' % oTab["explana"])
                    lstSigModels.append(u'        verbose_name = u"%s"' % oTab["explana"])
                    if oTab["unique_name"]:
                        lstSigModels.append(u'        unique_together = %s' % oTab["unique_name"])
                    if oTab["order_name"]:
                        lstSigModels.append(u'        ordering = %s' % oTab["order_name"])
                    lstSigModels.append(u'')
                    lstSigModels.append(u'    def __unicode__(self):')
                    if oTab["model_name"]:
                        lstSigModels.append(u'        return %s' % oTab["model_name"])
                    else:
                        lstSigModels.append(u'        return u""')

                    if oTab["is_user"]:
                        lstSigModels.append(u'')
                        lstSigModels.append(u'    def get_full_name(self):')
                        lstSigModels.append(u'        return self.username')
                        lstSigModels.append(u'')
                        lstSigModels.append(u'    def get_short_name(self):')
                        lstSigModels.append(u'        return self.username')
                        lstSigModels.append(u'')
                        lstSigModels.append(u'    @property')
                        lstSigModels.append(u'    def is_staff(self):')
                        lstSigModels.append(u'        return self.is_admin')

                    # lstSigAdmin.append(u'# %s样式定义' % oTab["explana"])
                    # lstSigAdmin.append(u'# class %sForm(ModelForm):' % oTab["className"])
                    # lstSigAdmin.append(u'#     class Meta:')
                    # lstSigAdmin.append(u'#         widgets = {')
                    # lstSigAdmin.append(u'#         }')
                    # lstSigAdmin.append(u'')
                    # lstSigAdmin.append(u'')

                    lstSigAdmin.append(u'# %s' % oTab["explana"])
                    lstSigAdmin.append(u'class %sAdmin(admin.ModelAdmin):' % oTab["className"])
                    lstSigAdmin.append(u'    list_display = %s' % str(lstFieldName))
                    lstSigAdmin.append(u'    # list_filter = []  # 过滤字段')
                    lstSigAdmin.append(u'    # list_editable = []  # 列表编辑字段')
                    lstSigAdmin.append(u'    # readonly_fields = []  # 只读字段')
                    lstSigAdmin.append(u'')
                    lstSigAdmin.append(u'    # def has_delete_permission(self, request, obj=None): # 去掉删除')
                    lstSigAdmin.append(u'    # def has_add_permission(self, request, obj=None): # 去掉增加')
                    lstSigAdmin.append(u'    # def formfield_for_foreignkey(self, db_field, request=None, **kwargs): # 过滤编辑页面外键')
                    lstSigAdmin.append(u'    # def formfield_for_manytomany(self, db_field, request, **kwargs): # 过滤manytomany外键')
                    lstSigAdmin.append(u'    # def delete_model(self, request, obj): # 删除单条')
                    lstSigAdmin.append(u'    # def delete_models(self, request, queryset): # 删除多条')
                    lstSigAdmin.append(u'    # def save_model(self, request, obj, form, change): # 保存')
                    lstSigAdmin.append(u'    # def save_related(self, request, form, formsets, change): # 保存关联表')
                    lstSigAdmin.append(u'    # def get_search_results(self, request, queryset, search_term): # 列表过滤')
                    lstSigAdmin.append(u'    # def get_fieldsets(self, request, obj=None): # 编辑页面显示字段')
                    lstSigAdmin.append(u'    # def _create_formsets(self, request, obj, change): # 编辑页面自定义检查重载函数')
                    lstSigAdmin.append(u'    # def formfield_for_dbfield(self, db_field, **kwargs): # 去掉外键增加、修改')
                    lstSigAdmin.append(u'')
                    lstSigAdmin.append(u'')

                    if oTab["auto_generate"]:
                        oOutoTable = dictAutoTable[oTab["autoId"]]
                        if oOutoTable["adminContent"]:
                            oRe = re.search('\[begin head\](.*)\[end head\]', oOutoTable["adminContent"], re.I | re.S)
                            if oRe:
                                head = oRe.groups()[0].strip()
                                if head:
                                    lstTmpHead = head.split("\r\n")
                                    for sHead in lstTmpHead:
                                        if '{models}' in sHead:
                                            className = re.search("import (.*)", sHead, re.I).groups()[0]
                                            if dictClassName_moduleName[className] != module:
                                                sHead = sHead.replace('{models}',
                                                                      "%s.models" % dictClassName_moduleName[className])
                                            else:
                                                sHead = sHead.replace('{models}', "models")

                                        elif '{project}' in sHead:
                                            sHead = sHead.replace('{project}', oTab["prjName"])

                                        if sHead not in lstAdminHead:
                                            lstAdminHead.append(sHead)

                            oRe = re.search('\[begin previous content\](.*)\[end previous content\]',
                                            oOutoTable["adminContent"],
                                            re.I | re.S)
                            if oRe:
                                content = oRe.groups()[0].strip("\r\n")
                                if content.strip():
                                    lstSigAdmin.insert(0, u"")
                                    lstSigAdmin.insert(0, content)

                            oRe = re.search('\[begin next content\](.*)\[end next content\]',
                                            oOutoTable["adminContent"], re.I | re.S)
                            if oRe:
                                content = oRe.groups()[0].strip("\r\n")
                                if content.strip():
                                    lstSigAdmin.append(u"")
                                    lstSigAdmin.append(content)

                        if oOutoTable["modelsContent"]:
                            oRe = re.search('\[begin head\](.*)\[end head\]', oOutoTable["modelsContent"], re.I | re.S)
                            if oRe:
                                head = oRe.groups()[0].strip()
                                if head:
                                    lstTmpHead = head.split("\r\n")
                                    for sHead in lstTmpHead:
                                        if '{models}' in sHead:
                                            className = re.search("import (.*)", sHead, re.I).groups()[0]
                                            if dictClassName_moduleName[className] != module:
                                                sHead = sHead.replace('{models}',
                                                                      "%s.models" % dictClassName_moduleName[className])
                                            else:
                                                sHead = sHead.replace('{models}', "models")

                                        elif '{project}' in sHead:
                                            sHead = sHead.replace('{project}', oTab["prjName"])

                                        if sHead not in lstModelsHead:
                                            lstModelsHead.append(sHead)

                            oRe = re.search('\[begin content\](.*)\[end content\]', oOutoTable["modelsContent"],
                                            re.I | re.S)
                            if oRe:
                                content = oRe.groups()[0].strip("\r\n")
                                if content.strip():
                                    lstSigModels.append(u"")
                                    lstSigModels.append(content)
                        pass

                    lstSigAdmin.append(u'admin.site.register(%s, %sAdmin)' % (oTab["className"], oTab["className"]))

                    # if oTab["generate_admin"]:
                    lstAdmin.extend(lstSigAdmin)
                    lstAdmin.append(u'')
                    lstAdmin.append(u'')

                    # if oTab["generate_models"]:
                    lstModels.extend(lstSigModels)
                    lstModels.append(u'')
                    lstModels.append(u'')

            lstModels.insert(0, u'')
            lstModels.insert(0, u'')
            for sModuleHead in lstModelsHead:
                lstModels.insert(0, sModuleHead)

            lstModels.insert(0, u'from django.db import models')
            lstModels.insert(0, u'')
            lstModels.insert(0, u'# -*- coding=utf-8 -*-')
            lstModels.insert(0, u'#!/usr/bin/python')
            lstModels.append(u'')
            fh = open(os.path.join(self.server_bak_path, module, 'models.py'), "wb")
            buf = u'\r\n'.join(lstModels)
            fh.write(buf.encode('utf-8'))
            fh.close()

            lstAdmin.insert(0, u'')
            lstAdmin.insert(0, u'')
            for sAdminHead in lstAdminHead:
                lstAdmin.insert(0, sAdminHead)

            lstAdmin.insert(0, u'from django.contrib import admin')
            lstAdmin.insert(0, u'')
            lstAdmin.insert(0, u'# -*- coding=utf-8 -*-')
            lstAdmin.insert(0, u'#!/usr/bin/python')
            lstAdmin.append(u'')
            fh = open(os.path.join(self.server_bak_path, module, 'admin.py'), "wb")
            buf = u'\r\n'.join(lstAdmin)
            fh.write(buf.encode('utf-8'))
            fh.close()

    def _makeField(self, className, field, lstModule, module, dictClassName_moduleName, lstField):
        lstPara = []
        if field["isNull"]:
            lstPara.append(u"blank=True")
            lstPara.append(u"null=True")

        if field["index"]:
            lstPara.append(u"db_index=True")

        if field["only"]:
            lstPara.append(u"unique=True")

        if field["type"] in ["2", "3"]:
            if field["timeOuto"] == "1":
                lstPara.append(u"auto_now_add=True")

            elif field["timeOuto"] == "2":
                lstPara.append(u"auto_now=True")

        if field["default"] not in [None, ""]:
            if field["type"] == "5":  # bool类型
                if field["default"].lower() == "true":
                    lstPara.append(u"default=True")

                elif field["default"].lower() == "false":
                    lstPara.append(u"default=False")

            else:
                lstPara.append(u"default=%s" % field["default"])

        if field["value"] not in [None, ""]:
            lstPara.append(u"choices=%s" % field["value"])

        if lstPara:
            sPara = "%s, " % ", ".join(lstPara)
        else:
            sPara = ""

        if field.has_key("selectForeignKey_className"):
            dict_foreignKey = {}
            for tmp_field in lstField:
                if tmp_field.has_key("selectForeignKey_className"):
                    if dict_foreignKey.has_key(tmp_field["selectForeignKey_className"]):
                        dict_foreignKey[tmp_field["selectForeignKey_className"]] += 1
                    else:
                        dict_foreignKey[tmp_field["selectForeignKey_className"]] = 1

            if dict_foreignKey[field["selectForeignKey_className"]] > 1:
                related_name = ", related_name='%s_%s_%s'" % (className.lower(), field["name"].lower(), field["selectForeignKey_className"].lower())
            else:
                related_name = ""

            if field["selectForeignKey_className"] == className:
                if field["help"] not in ["", None]:
                    sField = u"    %s = models.ForeignKey('self', %sverbose_name=u'%s'%s, help_text=u'%s')" % (
                        field["name"], sPara, field["explana"], related_name, field["help"])
                else:
                    sField = u"    %s = models.ForeignKey('self', %sverbose_name=u'%s'%s)" % (
                        field["name"], sPara, field["explana"], related_name)
            else:
                if field["help"] not in ["", None]:
                    sField = u"    %s = models.ForeignKey(%s, %sverbose_name=u'%s'%s, help_text=u'%s')" % (
                        field["name"], field["selectForeignKey_className"], sPara, field["explana"], related_name, field["help"])
                else:
                    sField = u"    %s = models.ForeignKey(%s, %sverbose_name=u'%s'%s)" % (
                        field["name"], field["selectForeignKey_className"], sPara, field["explana"], related_name)

                tmp_module = dictClassName_moduleName[field["selectForeignKey_className"]]
                if module != tmp_module:
                    sImportModule = u"from %s.models import %s" % (tmp_module, field["selectForeignKey_className"])
                    if sImportModule not in lstModule:
                        lstModule.append(sImportModule)

        elif field["type"] == "0":  # varchar
            if field["help"] not in ["", None]:
                sField = u"    %s = models.CharField(max_length=%s, %sverbose_name=u'%s', help_text=u'%s')" % (
                    field["name"], field["length"], sPara, field["explana"], field["help"])
            else:
                sField = u"    %s = models.CharField(max_length=%s, %sverbose_name=u'%s')" % (
                    field["name"], field["length"], sPara, field["explana"])

        elif field["type"] == "1":  # integer
            if field["help"] not in ["", None]:
                sField = u"    %s = models.IntegerField(%sverbose_name=u'%s', help_text=u'%s')" % (
                    field["name"], sPara, field["explana"], field["help"])
            else:
                sField = u"    %s = models.IntegerField(%sverbose_name=u'%s')" % (
                    field["name"], sPara, field["explana"])

        elif field["type"] == "10":  # 无符号integer
            if field["help"] not in ["", None]:
                sField = u"    %s = models.PositiveIntegerField(%sverbose_name=u'%s', help_text=u'%s')" % (
                    field["name"], sPara, field["explana"], field["help"])
            else:
                sField = u"    %s = models.PositiveIntegerField(%sverbose_name=u'%s')" % (
                    field["name"], sPara, field["explana"])

        elif field["type"] == "2":  # datetime
            if field["help"] not in ["", None]:
                sField = u"    %s = models.DateTimeField(%sverbose_name=u'%s', help_text=u'%s')" % (
                    field["name"], sPara, field["explana"], field["help"])
            else:
                sField = u"    %s = models.DateTimeField(%sverbose_name=u'%s')" % (
                    field["name"], sPara, field["explana"])

        elif field["type"] == "3":  # date
            if field["help"] not in ["", None]:
                sField = u"    %s = models.DateField(%sverbose_name=u'%s', help_text=u'%s')" % (
                    field["name"], sPara, field["explana"], field["help"])
            else:
                sField = u"    %s = models.DateField(%sverbose_name=u'%s')" % (field["name"], sPara, field["explana"])

        elif field["type"] == "9":  # time
            if field["help"] not in ["", None]:
                sField = u"    %s = models.TimeField(%sverbose_name=u'%s', help_text=u'%s')" % (
                    field["name"], sPara, field["explana"], field["help"])
            else:
                sField = u"    %s = models.TimeField(%sverbose_name=u'%s')" % (field["name"], sPara, field["explana"])

        elif field["type"] == "4":  # text
            if field["help"] not in ["", None]:
                sField = u"    %s = models.TextField(%sverbose_name=u'%s', help_text=u'%s')" % (
                    field["name"], sPara, field["explana"], field["help"])
            else:
                sField = u"    %s = models.TextField(%sverbose_name=u'%s')" % (field["name"], sPara, field["explana"])

        elif field["type"] == "5":  # bool
            if field["help"] not in ["", None]:
                sField = u"    %s = models.BooleanField(%sverbose_name=u'%s', help_text=u'%s')" % (
                    field["name"], sPara, field["explana"], field["help"])
            else:
                sField = u"    %s = models.BooleanField(%sverbose_name=u'%s')" % (
                    field["name"], sPara, field["explana"])

        elif field["type"] == "6":  # bool
            if field["help"] not in ["", None]:
                sField = u"    %s = models.FloatField(%sverbose_name=u'%s', help_text=u'%s')" % (
                    field["name"], sPara, field["explana"], field["help"])
            else:
                sField = u"    %s = models.FloatField(%sverbose_name=u'%s')" % (field["name"], sPara, field["explana"])

        elif field["type"] == "7":  # image
            if field["help"] not in ["", None]:
                sField = u"    %s = models.ImageField(upload_to='images/', storage=ImageStorage(), %sverbose_name=u'%s', help_text=u'%s')" % (
                    field["name"], sPara, field["explana"], field["help"])
            else:
                sField = u"    %s = models.ImageField(upload_to='images/', storage=ImageStorage(), %sverbose_name=u'%s')" % (
                    field["name"], sPara, field["explana"])

            if u'from utils.storage import *' not in lstModule:
                lstModule.append(u'from utils.storage import *')

        elif field["type"] == "8":  # file
            if field["help"] not in ["", None]:
                sField = u"    %s = models.FileField(upload_to='files/', storage=ImageStorage(), %sverbose_name=u'%s', help_text=u'%s')" % (
                    field["name"], sPara, field["explana"], field["help"])
            else:
                sField = u"    %s = models.FileField(upload_to='files/', storage=ImageStorage(), %sverbose_name=u'%s')" % (
                    field["name"], sPara, field["explana"])

            if u'from utils.storage import *' not in lstModule:
                lstModule.append(u'from utils.storage import *')

        return sField

    def make_settings(self, prjName, dictModule):
        lstLine = []
        lstLine.append(u"#!/usr/bin/python")
        lstLine.append(u"# -*- coding=utf-8 -*-")
        lstLine.append(u"")
        lstLine.append(u"import os")
        lstLine.append(u"from platform import platform")
        lstLine.append(u"")
        lstLine.append(u"if 'centos' in platform():")
        lstLine.append(u"    DEBUG = False")
        lstLine.append(u"else:")
        lstLine.append(u"    DEBUG = True")
        lstLine.append(u"")
        lstLine.append(u"TEMPLATE_DEBUG = DEBUG")
        lstLine.append(u"BASE_DIR = os.path.dirname(os.path.dirname(__file__))")

        chars = 'abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)'
        lstLine.append(u"SECRET_KEY = '%s'" % get_random_string(50, chars))
        lstLine.append(u"ALLOWED_HOSTS = ['localhost', '127.0.0.1']")
        lstLine.append(u"")
        lstLine.append(u"TEMPLATE_DIRS = (")
        lstLine.append(u"    os.path.join(BASE_DIR, 'templates'),")
        lstLine.append(u")")
        lstLine.append(u"")
        lstLine.append(u"INSTALLED_APPS = (")

        lstLine.append(u"   'django.contrib.auth',")
        lstLine.append(u"   'django.contrib.contenttypes',")
        lstLine.append(u"   'django.contrib.sessions',")
        lstLine.append(u"   'django.contrib.messages',")
        lstLine.append(u"   'django.contrib.staticfiles',")
        lstLine.append(u"   'suit',")
        lstLine.append(u"   'django.contrib.admin',")
        lstLine.append(u"   # 'DjangoUeditor',")
        lstLine.append(u"   # 'django_select2',")

        lstModule = dictModule.keys()
        for name_en in lstModule:
            lstLine.append(u"   '%s'," % (name_en))
        lstLine.append(u")")
        lstLine.append(u"")
        # lstLine.append(u"from django.conf.global_settings import TEMPLATE_CONTEXT_PROCESSORS as TCP")
        # lstLine.append(u"TEMPLATE_CONTEXT_PROCESSORS = TCP + (")
        # lstLine.append(u"    'django.core.context_processors.request',")
        # lstLine.append(u")")
        # lstLine.append(u"")
        lstLine.append(u"MIDDLEWARE = (")
        lstLine.append(u"    'django.middleware.security.SecurityMiddleware',")
        lstLine.append(u"    'django.contrib.sessions.middleware.SessionMiddleware',")
        lstLine.append(u"    'django.middleware.common.CommonMiddleware',")
        lstLine.append(u"    'django.contrib.auth.middleware.AuthenticationMiddleware',")
        lstLine.append(u"    'django.contrib.messages.middleware.MessageMiddleware',")
        lstLine.append(u"    'django.middleware.clickjacking.XFrameOptionsMiddleware',")
        lstLine.append(u")")
        lstLine.append(u"")
        # lstLine.append(u"TEMPLATE_CONTEXT_PROCESSORS = (")
        # lstLine.append(u"    'django.contrib.auth.context_processors.auth',")
        # lstLine.append(u"    'django.core.context_processors.debug',")
        # lstLine.append(u"    'django.core.context_processors.i18n',")
        # lstLine.append(u"    'django.core.context_processors.media',")
        # lstLine.append(u"    'django.core.context_processors.static',")
        # lstLine.append(u"    'django.core.context_processors.request',")
        # lstLine.append(u"    'django.contrib.messages.context_processors.messages'")
        # lstLine.append(u")")
        # lstLine.append(u"")
        lstLine.append(u"SUIT_CONFIG = {")
        lstLine.append(u"    'ADMIN_NAME': u'管理平台',")
        lstLine.append(u"    'HEADER_DATE_FORMAT': 'Y年 F j日 l',")
        lstLine.append(u"    'LIST_PER_PAGE': 50,")
        lstLine.append(u"    'MENU': (")
        for name_en in lstModule:
            lstLine.append(u"        {'app': '%s', 'label': u'%s', 'icon': 'icon-user',}," % (
                name_en.lower(), dictModule[name_en]["name_ch"]))
        lstLine.append(u"    )")
        lstLine.append(u"}")
        lstLine.append(u"")
        # lstLine.append(u"UEDITOR_SETTINGS = {")
        # lstLine.append(u"    'toolbars': {")
        # lstLine.append(u"    },")
        # lstLine.append(u"    'images_upload': {")
        # lstLine.append(u"        'allow_type': 'jpeg,jpg,png,gif',")
        # lstLine.append(u"        'max_size': '3222kb'")
        # lstLine.append(u"    },")
        # lstLine.append(u"    'files_upload': {")
        # lstLine.append(u"        'allow_type': 'doc',")
        # lstLine.append(u"        'max_size': '2222kb'")
        # lstLine.append(u"    }")
        # lstLine.append(u"}")
        # lstLine.append(u"")
        lstLine.append(u"ROOT_URLCONF = '%s.urls'" % prjName)
        lstLine.append(u"")
        lstLine.append(u"TEMPLATES = [")
        lstLine.append(u"    {")
        lstLine.append(u"        'BACKEND': 'django.template.backends.django.DjangoTemplates',")
        lstLine.append(u"        'DIRS': [os.path.join(BASE_DIR, 'templates')],")
        lstLine.append(u"        'APP_DIRS': True,")
        lstLine.append(u"        'OPTIONS': {")
        lstLine.append(u"            'context_processors': [")
        lstLine.append(u"                'django.template.context_processors.debug',")
        lstLine.append(u"                'django.template.context_processors.request',")
        lstLine.append(u"                'django.contrib.auth.context_processors.auth',")
        lstLine.append(u"                'django.contrib.messages.context_processors.messages',")
        lstLine.append(u"            ],")
        lstLine.append(u"        },")
        lstLine.append(u"    },")
        lstLine.append(u"]")
        lstLine.append(u"")
        lstLine.append(u"WSGI_APPLICATION = '%s.wsgi.application'" % prjName)
        lstLine.append(u"")
        lstLine.append(u"if DEBUG:")
        lstLine.append(u"    HOST = '127.0.0.1'")
        lstLine.append(u"    DB_NAME = '%s'" % prjName)
        lstLine.append(u"    DB_USER = 'root'")
        lstLine.append(u"    DB_PWD = '123456'")
        lstLine.append(u"else:")
        lstLine.append(u"    HOST = '121.42.178.20'")
        lstLine.append(u"    DB_NAME = '%s'" % prjName)
        lstLine.append(u"    DB_USER = 'root'")
        lstLine.append(u"    DB_PWD = 'qv8sqntqmmv5'")
        lstLine.append(u"")
        lstLine.append(u"DATABASES = {")
        lstLine.append(u"    'default': {")
        lstLine.append(u"        'ENGINE': 'django.db.backends.mysql',")
        lstLine.append(u"        'NAME': DB_NAME,")
        lstLine.append(u"        'USER': DB_USER,")
        lstLine.append(u"        'PASSWORD': DB_PWD,")
        lstLine.append(u"        'HOST': HOST,")
        lstLine.append(u"        'PORT': '3306',")
        lstLine.append(u"    }")
        lstLine.append(u"}")
        lstLine.append(u"")
        lstLine.append(u"SITE_ID = 1")
        lstLine.append(u"LANGUAGE_CODE = 'zh-hans'")
        lstLine.append(u"TIME_ZONE = 'Asia/Shanghai'")
        lstLine.append(u"USE_I18N = True")
        lstLine.append(u"USE_L10N = True")
        lstLine.append(u"USE_TZ = False")
        # lstLine.append(u"")
        lstLine.append(u"DATE_FORMAT = 'Y-m-d'")
        lstLine.append(u"DATETIME_FORMAT = 'Y-m-d H:i'")
        lstLine.append(u"TIME_FORMAT = 'H:i'")
        lstLine.append(u"STATIC_URL = '/static/'")
        lstLine.append(u"STATICFILES_DIRS = (")
        lstLine.append(u"    os.path.join(BASE_DIR, 'static'),")
        lstLine.append(u")")
        lstLine.append(u"MEDIA_URL = '/media/'")
        lstLine.append(u"MEDIA_ROOT = os.path.join(BASE_DIR, 'media')")
        lstLine.append(u"")
        # lstLine.append(u"STATICFILES_FINDERS = (")
        # lstLine.append(u"    'django.contrib.staticfiles.finders.FileSystemFinder',")
        # lstLine.append(u"    'django.contrib.staticfiles.finders.AppDirectoriesFinder',")
        # lstLine.append(u")")
        # lstLine.append(u"")
        # lstLine.append(u"TEMPLATE_LOADERS = (")
        # lstLine.append(u"    'django.template.loaders.filesystem.Loader',")
        # lstLine.append(u"    'django.template.loaders.app_directories.Loader',")
        # lstLine.append(u")")
        # lstLine.append(u"")
        lstLine.append(u"LOGGING = {")
        lstLine.append(u"    'version': 1,")
        lstLine.append(u"    'disable_existing_loggers': True,")
        lstLine.append(u"    'formatters': {")
        lstLine.append(u"        'standard': {")
        lstLine.append(
            u"            'format': '%(asctime)s [%(threadName)s:%(thread)d] [%(name)s:%(lineno)d] [%(levelname)s]- %(message)s'")
        lstLine.append(u"        },")
        lstLine.append(u"    },")
        lstLine.append(u"    'filters': {")
        lstLine.append(u"    },")
        lstLine.append(u"    'handlers': {")
        lstLine.append(u"        'mail_admins': {")
        lstLine.append(u"            'level': 'ERROR',")
        lstLine.append(u"            'class': 'django.utils.log.AdminEmailHandler',")
        lstLine.append(u"            'include_html': True,")
        lstLine.append(u"        },")
        lstLine.append(u"        'default': {")
        lstLine.append(u"            'level': 'INFO',")
        lstLine.append(u"            'class': 'logging.handlers.RotatingFileHandler',")
        lstLine.append(u"            'filename': os.path.join(BASE_DIR + '/logs/', '%s.log')," % prjName)
        lstLine.append(u"            'maxBytes': 1024 * 1024 * 5,  # 5 MB")
        lstLine.append(u"            'backupCount': 10,")
        lstLine.append(u"            'formatter': 'standard',")
        lstLine.append(u"        },")
        lstLine.append(u"        'console': {")
        lstLine.append(u"            'level': 'INFO',")
        lstLine.append(u"            'class': 'logging.StreamHandler',")
        lstLine.append(u"            'formatter': 'standard'")
        lstLine.append(u"        },")
        lstLine.append(u"        'request_handler': {")
        lstLine.append(u"            'level': 'DEBUG',")
        lstLine.append(u"            'class': 'logging.handlers.RotatingFileHandler',")
        lstLine.append(u"            'filename': os.path.join(BASE_DIR + '/logs/', '%s.log')," % prjName)
        lstLine.append(u"            'maxBytes': 1024 * 1024 * 5,  # 5 MB")
        lstLine.append(u"            'backupCount': 10,")
        lstLine.append(u"            'formatter': 'standard',")
        lstLine.append(u"        },")
        lstLine.append(u"        'scprits_handler': {")
        lstLine.append(u"            'level': 'DEBUG',")
        lstLine.append(u"            'class': 'logging.handlers.RotatingFileHandler',")
        lstLine.append(u"            'filename': os.path.join(BASE_DIR + '/logs/', '%s.log')," % prjName)
        lstLine.append(u"            'maxBytes': 1024 * 1024 * 5,  # 5 MB")
        lstLine.append(u"            'backupCount': 10,")
        lstLine.append(u"            'formatter': 'standard',")
        lstLine.append(u"        },")
        lstLine.append(u"    },")
        lstLine.append(u"    'loggers': {")
        lstLine.append(u"        'django': {")
        lstLine.append(u"            'handlers': ['default', 'console'],")
        lstLine.append(u"            'level': 'DEBUG',")
        lstLine.append(u"            'propagate': False")
        lstLine.append(u"        },")
        lstLine.append(u"        '': {")
        lstLine.append(u"            'handlers': ['default', 'console'],")
        lstLine.append(u"            'level': 'DEBUG',")
        lstLine.append(u"            'propagate': True")
        lstLine.append(u"        },")
        lstLine.append(u"        'django.request': {")
        lstLine.append(u"            'handlers': ['request_handler'],")
        lstLine.append(u"            'level': 'DEBUG',")
        lstLine.append(u"            'propagate': False")
        lstLine.append(u"        },")
        lstLine.append(u"        'scripts': {")
        lstLine.append(u"            'handlers': ['scprits_handler'],")
        lstLine.append(u"            'level': 'INFO',")
        lstLine.append(u"            'propagate': False")
        lstLine.append(u"        },")
        lstLine.append(u"    }")
        lstLine.append(u"}")
        lstLine.append(u"")
        if self.user_models:
            lstLine.append(u"AUTH_USER_MODEL = '%s' # 自定义" % self.user_models)
            lstLine.append(u"# AUTH_USER_MODEL = 'auth.User' # 系统")
        else:
            lstLine.append(u"AUTH_USER_MODEL = 'auth.User' # 系统")
        lstLine.append(u"")

        sPath = os.path.abspath(os.path.join(self.prj_bak_path, u"settings.py"))
        fh = open(sPath, "wb")
        buf = u'\r\n'.join(lstLine)
        fh.write(buf.encode('utf-8'))
        fh.close()


BASE_URL = u"http://zh.whhuiyu.com"

# 工程目录，api下面的json会自动覆盖
SERVER_PATH = u'D:\\code\\lets2017'

# 备份目录，除api，其它都生成在这个目录下
SERVER_BAK_PATH = u'D:\\code\\lets2017_bak'

# 登录综合平台的用户名和密码
USER = u'XXXX'
PWD = u'XXXX'


# 工程名称，和工程中对应
PROJECT_NAME = u'lets2017'

# 没有参数，全部模块生成，参数一:模块名称
if __name__ == "__main__":
    lstPara = sys.argv
    if len(lstPara) == 1:
        oMakeCode = MakeCode(USER, PWD, SERVER_PATH, SERVER_BAK_PATH, PROJECT_NAME, None, BASE_URL)
    else:
        oMakeCode = MakeCode(USER, PWD, SERVER_PATH, SERVER_BAK_PATH, PROJECT_NAME, lstPara[1], BASE_URL)

    oMakeCode.make()
