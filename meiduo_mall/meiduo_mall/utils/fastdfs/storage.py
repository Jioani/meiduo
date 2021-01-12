from django.core.files.storage import Storage
from fdfs_client.client import Fdfs_client
from django.conf import settings


class FastDFSStorage(Storage):
    def _save(self, name, content):
        # name: 上传文件的名称
        # content: 包含上传文件内容的File对象，content.read()获取上传文件内容

        # 创建 Fdfs_client 对象
        client = Fdfs_client(settings.FDFS_CLIENT_CONF)

        # 上传文件到 FastDFS 系统
        res = client.upload_by_buffer(content.read())
        if res.get("Status") != "Upload successed.":
            raise Exception("上传文件到FDFS系统失败")
        file_id = res.get("Remote file_id")
        return file_id

    def exists(self, name):
        return False

    def url(self, name):
        return settings.FDFS_URL + name
