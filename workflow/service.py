# -*- coding: utf-8 -*-
from xml.etree import ElementTree

from workflow.models import FlowNode, FlowTrans
from docx import Document
from django.conf import settings
import os
import logging
logger = logging.getLogger(__name__)


def bpmn_parse(xml_text):
    """
    解析bpmn格式文件
    :param xml_text:
    :return:
    """
    ns = {
        'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
        'bpmn': 'http://www.omg.org/spec/BPMN/20100524/MODEL',
        'bpmndi': 'http://www.omg.org/spec/BPMN/20100524/DI',
        'dc': 'http://www.omg.org/spec/DD/20100524/DC',
        'di': 'http://www.omg.org/spec/DD/20100524/DI'
    }
    nodes = []
    trans = []
    root = ElementTree.fromstring(xml_text)
    process = list(root)[0]
    # 环节
    tasks = process.findall('bpmn:task', ns)
    # 流转
    sequences = process.findall('bpmn:sequenceFlow', ns)

    for task in tasks:
        nodes.append(task.attrib)

    for sequence in sequences:
        trans.append(sequence.attrib)

    return nodes, trans


def flow_nodes(flow_id):
    """
    获取流程环节信息
    :param flow_id:
    :return:
    """
    qs = FlowNode.objects.filter(flow_id=flow_id, del_flag=0).order_by('name')
    node_list = []

    for node in qs:
        if node.process:
            process = {
                'id': node.process.id, 'name': node.process.name, 'type': node.process.type,
                'image': node.process.image.url if node.process.image else None
            }
        else:
            process = None
        node_list.append({
            'id': node.id, 'name': node.name, 'look_on': node.look_on, 'step': node.step, 'task_id': node.task_id,
            'condition': node.condition, 'process': process
        })

    return node_list


def get_start_node(flow_id):
    """
    获取流程第一个环节
    :param flow_id:
    :return:
    """
    transition = FlowTrans.objects.filter(flow_id=flow_id, incoming__startswith='StartEvent').first()

    if transition:
        node = FlowNode.objects.filter(flow_id=flow_id, task_id=transition.outgoing).first()

        if node:
            return node.id
    return None


def get_end_node(flow_id):
    """
    获取流程第一个环节
    :param flow_id:
    :return:
    """
    transition = FlowTrans.objects.filter(flow_id=flow_id, outgoing__startswith='EndEvent').first()

    if transition:
        node = FlowNode.objects.filter(flow_id=flow_id, task_id=transition.incoming).first()

        if node:
            return node.id
    return None


def bpmn_color(xml, tasks):
    """
    解析bpmn格式文件,对环节着色
    :param xml_text:
    :return:
    """
    xml = xml.replace('bpmn:definitions',
                      'bpmn:definitions xmlns:bioc="http://bpmn.io/schema/bpmn/biocolor/1.0"', 1)
    if len(tasks) > 0:
        last_task_id = tasks[-1]
        for task_id in tasks:
            old = 'bpmnElement="{}"'.format(task_id)
            if task_id == last_task_id:
                new = 'bpmnElement="{}" bioc:stroke="#FE2E2E" bioc:fill="#F8E0E0"'.format(task_id)
            else:
                new = 'bpmnElement="{}" bioc:stroke="#1E88E5" bioc:fill="#BBDEFB"'.format(task_id)
            xml = xml.replace(old, new, 1)
    # print xml
    return xml


def flow_doc_save(flow_id, name, content):
    """
    保存应用模板生成文件
    :param content: 内容
    :return:
    """
    path = ''
    try:
        # 打开文档
        document = Document()
        # 添加文本
        # document.add_paragraph(content)   改成下面这样就可以保存中文字体了， fuck
        document.add_paragraph('%s' % content)
        # 保存文件
        media = settings.MEDIA_ROOT
        path = u'{}/workflow/{}'.format(media, flow_id)
        is_exists = os.path.exists(path)
        if not is_exists:
            os.makedirs(path)
        media_path = u'{}/{}'.format(path, name)
        logger.info(media_path)
        document.save(media_path)
        path = u'workflow/{}/{}'.format(flow_id, name)
    except Exception as e:
        logger.exception(u'flow_doc_save Exception:{}'.format(str(e)))
    return path
