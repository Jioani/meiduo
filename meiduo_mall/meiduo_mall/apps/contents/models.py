from django.db import models
from meiduo_mall.utils.base_model import BaseModel


class ContentCategory(BaseModel):
    name = models.CharField(max_length=50, verbose_name="名称")
    key = models.CharField(max_length=50, verbose_name="类键名")

    class Meta:
        db_table = "tb_content_category"
        verbose_name = "广告类别"


class Content(BaseModel):
    category = models.ForeignKey(ContentCategory, on_delete=models.PROTECT, verbose_name="类别")
    title = models.CharField(max_length=100, verbose_name="标题")
    url = models.CharField(max_length=100, verbose_name="链接地址")
    image = models.ImageField(null=True, blank=True, verbose_name="广告图片")
    text = models.TextField(null=True, blank=True, verbose_name="广告内容")
    sequence = models.IntegerField(verbose_name="排序")
    status = models.BooleanField(default=True, verbose_name="是否展示")

    class Meta:
        db_table = "tb_content"
        verbose_name = "广告内容"
