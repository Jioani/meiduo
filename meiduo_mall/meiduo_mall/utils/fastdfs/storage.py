from django.core.files.storage import Storage
from fdfs_client.client import Fdfs_client
from django.conf import settings


class FastDFSStorage(Storage):
    def _save(self):
        client = Fdfs_client()

    def exists(self, name):
        return False
