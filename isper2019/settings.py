#!/usr/bin/python
# -*- coding=utf-8 -*-

import os
from platform import platform

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

DEBUG = True
if 'Linux-4.4.0-146-generic-x86_64-with-Ubuntu-16.04-xenial' in platform():
    isLiveServer = True
else:
    isLiveServer = False

SECRET_KEY = '#rt$+y+(lkuz-aollrb8arheykm(6=gr%n%a1sqzf2_pf3)0f#'
ALLOWED_HOSTS = ['*']

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'suit',
    'django.contrib.admin',
    'corsheaders',
    'advertising',
    # 'DjangoUeditor',
    # 'django_select2',
    'account',
    'workflow',
    'group',
    'system',
    'project',
    'course',
    'experiment',
    'team',
    'cms',
    'business',
    'socketio'
)

MIDDLEWARE = (
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'isper2019.middleware.LogMiddleware'
)

SUIT_CONFIG = {
    'ADMIN_NAME': u'管理平台',
    'HEADER_DATE_FORMAT': 'Y年 F j日 l',
    'LIST_PER_PAGE': 50,
    'MENU': (
        {'app': 'account', 'label': u'用户', 'icon': 'icon-user', },
        # {'app': 'task', 'label': u'实验任务', 'icon': 'icon-user', },
        {'app': 'workflow', 'label': u'流程', 'icon': 'icon-user', },
        {'app': 'system', 'label': u'系统', 'icon': 'icon-user', },
        # {'app': 'project', 'label': u'项目', 'icon': 'icon-user', },
        {'app': 'course', 'label': u'课程', 'icon': 'icon-user', },
        {'app': 'experiment', 'label': u'实验', 'icon': 'icon-user', },
        # {'app': 'team', 'label': u'小组', 'icon': 'icon-user', },
        {'app': 'cms', 'label': u'内容管理', 'icon': 'icon-user', },
    )
}

CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_CREDENTIALS = True
CORS_ORIGIN_WHITELIST = (
     # 'localhost:8080',
     # '127.0.0.1:8080',
     # '39.107.122.234:8080'
)

ROOT_URLCONF = 'isper2019.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'isper2019.wsgi.application'

HOST = '39.107.122.234'
DB_NAME = 'isper2019'
DB_USER = 'remote'
DB_PWD = 'remoteadmin'

# HOST = 'localhost'
# DB_NAME = 'isper2019'
# DB_USER = 'root'
# DB_PWD = ''

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': DB_NAME,
        'USER': DB_USER,
        'PASSWORD': DB_PWD,
        'HOST': HOST,
        'PORT': '3306',
        # 'OPTIONS': {'charset': 'utf8mb4'},
    }
}

CACHE_HOST = '127.0.0.1:11211'

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': CACHE_HOST,
        'TIMEOUT': 43200,
        'OPTIONS': {
            'MAX_ENTRIES': 5000
        }
    }
}

SITE_ID = 1
LANGUAGE_CODE = 'zh-hans'
TIME_ZONE = 'Asia/Shanghai'
USE_I18N = True
USE_L10N = True
USE_TZ = True
DATE_FORMAT = 'Y-m-d'
DATETIME_FORMAT = 'Y-m-d H:i'
TIME_FORMAT = 'H:i'
STATIC_URL = '/static/'
STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'static'),
)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
if isLiveServer:
    STATIC_ROOT = os.path.join(BASE_DIR, 'static')

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(threadName)s:%(thread)d] [%(name)s:%(lineno)d] [%(levelname)s]- %(message)s'
        },
    },
    'filters': {
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
            'include_html': True,
        },
        'default': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR + '/logs/', 'isper2019.log'),
            'maxBytes': 1024 * 1024 * 5,  # 5 MB
            'backupCount': 10,
            'formatter': 'standard',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'standard'
        },
        'request_handler': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR + '/logs/', 'isper2019.log'),
            'maxBytes': 1024 * 1024 * 5,  # 5 MB
            'backupCount': 10,
            'formatter': 'standard',
        },
        'scprits_handler': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR + '/logs/', 'isper2019.log'),
            'maxBytes': 1024 * 1024 * 5,  # 5 MB
            'backupCount': 10,
            'formatter': 'standard',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['default', 'console'],
            'level': 'DEBUG',
            'propagate': False
        },
        '': {
            'handlers': ['default', 'console'],
            'level': 'DEBUG',
            'propagate': True
        },
        'django.request': {
            'handlers': ['request_handler'],
            'level': 'ERROR',
            'propagate': False
        },
        'scripts': {
            'handlers': ['scprits_handler'],
            'level': 'INFO',
            'propagate': False
        },
    }
}

AUTH_USER_MODEL = 'account.Tuser'  # 自定义
# AUTH_USER_MODEL = 'auth.User' # 系统
