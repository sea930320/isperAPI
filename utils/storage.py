# -*- coding: utf-8 -*-
from django.core.files.storage import FileSystemStorage
from django.core.exceptions import SuspiciousOperation
from django.conf import settings
from django.core.files.base import ContentFile
# from PIL import Image
# import const
import StringIO

from django.utils.encoding import force_text


class Storage(FileSystemStorage):
    def __init__(self, location=settings.MEDIA_ROOT, base_url=settings.MEDIA_URL):
        super(Storage, self).__init__(location, base_url)

    @property
    def maxsize(self):
        return 5 * 1024 * 1024

    @property
    def filetypes(self):
        return []

    def delete(self, name):
        super(Storage, self).delete(name)


class FileStorage(Storage):
    @property
    def maxsize(self):
        return 20 * 1024 * 1024

    @property
    def filetypes(self):
        return ['doc', 'xls', 'docs', 'swf', 'amr', 'jpg', 'jpeg', 'png', 'gif']

    def _save(self, name, content):
        ext = name.split(".")[-1]
        # 类型判断
        # if self.filetypes != '*':
        #     if ext.lower() not in self.filetypes:
        #         raise SuspiciousOperation('file type error!')

        # 大小判断
        if content.size > self.maxsize:
            raise SuspiciousOperation('file size error!')

        return super(FileStorage, self)._save(name, content)


class ImageStorage(Storage):
    @property
    def maxsize(self):
        return 5 * 1024 * 1024

    @property
    def filetypes(self):
        return ['jpg', 'jpeg', 'png', 'gif', 'swf']

        # def _save(self, name, content):
        #     ext = name.split(".")[-1]
        #     #类型判断
        #     if self.filetypes != '*':
        #         if ext.lower() not in self.filetypes:
        #             raise SuspiciousOperation(const.IMAGES_EXT_ERROR_CODE)
        #
        #     #大小判断
        #     if content.size > self.maxsize:
        #         raise SuspiciousOperation(const.IMAGES_SIZE_ERROR_CODE)
        #
        #     return super(ImageStorage, self)._save(name, content)


# class ThumbStorage(ImageStorage):
#
#     def _save(self, name, content):
#         image = Image.open(content)
#         if image.mode not in ('L', 'RGB'):
#             image = image.convert('RGB')
#
#         width, height = image.size
#         size = 320
#         if width > size:
#             delta = width / size
#             height = int(height / delta)
#             image.thumbnail((size, height), Image.ANTIALIAS)
#
#         output = StringIO.StringIO()
#         image.save(output, 'JPEG')
#         co = ContentFile(output.getvalue())
#         output.close()
#
#         return super(ThumbStorage, self)._save(name, co)


class CheckSumFileStoreage(FileSystemStorage):
    """
    Md5 checksum filesystem storage
    """

    def get_available_name(self, name, max_length=None):
        if max_length and len(name) > max_length:
            raise (Exception("name's length is greater than max_length"))
        return force_text(name.replace('\\', '/'))

    def _save(self, name, content):
        if self.exists(name):
            return name
        return super(CheckSumFileStoreage, self)._save(name, content)

    # def exists(self, name):
    #     pass
