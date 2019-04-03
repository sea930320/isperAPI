#!/usr/bin/python
# coding:utf-8

from django.shortcuts import render


def index(request):
    return render(request, 'api/index.html')


def docs(request):
    return render(request, 'api/docs.json')


def module(request, json):
    return render(request, 'api/%s.json' % json)
