import json

from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import render
from django.views import View

import meiduo_mall.utils.mixins
from django_redis import get_redis_connection

from goods.models import GoodsCategory, SKU
from goods.utils import get_breadcrumb


# GET /list/(?P<category_id>\d+)/skus/
from meiduo_mall.utils.mixins import LoginRequiredMixin


class SKUListView(View):
    def get(self, request, category_id):
        page = request.GET.get("page", 1)
        page_size = request.GET.get("page_size", 10)
        ordering = request.GET.get("ordering", "-create_time")
        try:
            cat3 = GoodsCategory.objects.get(id=category_id)
        except Exception as e:
            return JsonResponse({"code": 400,
                                 "message": "查询不到此数据"})
        try:
            breadcrumb = get_breadcrumb(cat3)
        except Exception as e:
            return JsonResponse({"code": 400,
                                 "message": "获取面包屑导航数据出错"})
        try:
            skus = SKU.objects.filter(category_id=category_id,
                                      is_launched=True).order_by(ordering)
        except Exception as e:
            return JsonResponse({"code": 400,
                                 "message": "分类SKU商品数据获取出错"})
        paginator = Paginator(skus, page_size)
        result = paginator.get_page(page)
        sku_li = []
        for sku in result:
            sku_li.append({
                "id": sku.id,
                "name": sku.name,
                "price": sku.price,
                "comments": sku.comments,
                "default_image_url": "http://192.168.19.131:8888/" + sku.default_image.name
            })
        return JsonResponse({"code": 0,
                             "message": "OK",
                             "breadcrumb": breadcrumb,
                             "count": paginator.num_pages,
                             "list": sku_li})


class SKUHotView(View):
    def get(self, request, category_id):
        try:
            cat3 = GoodsCategory.objects.get(id=category_id)
        except Exception as e:
            return JsonResponse({"code": 400,
                                 "message": "查询不到此数据"})
        try:
            skus = SKU.objects.filter(category_id=category_id,
                                      is_launched=True).order_by("-sales")
        except Exception as e:
            return JsonResponse({"code": 400,
                                 "message": "分类SKU商品数据获取出错"})
        hot_skus = []
        i = 0
        for sku in skus:
            if i < 2:
                hot_skus.append({
                    "id": sku.id,
                    "name": sku.name,
                    "price": sku.price,
                    "default_image_url": "http://192.168.19.131:8888/" + sku.default_image.name
                })
                i += 1
        return JsonResponse({"code": 0,
                             "message": "OK",
                             "hot_skus": hot_skus})


class BrowserHistoryView(LoginRequiredMixin, View):
    def post(self, request):
        req_data = json.loads(request.body)
        sku_id = req_data.get("sku_id")
        try:
            redis_conn = get_redis_connection("history")
            redis_conn.lrem(request.user.id, 0, sku_id)
            redis_conn.lpush(request.user.id, sku_id)
            redis_conn.ltrim(request.user.id, 0, 4)
        except Exception as e:
            return JsonResponse({"code": 400,
                                 "message": "操作数据库失败"})
        return JsonResponse({"code": 0,
                             "message": "OK"})

    def get(self, request):
        redis_conn = get_redis_connection("history")
        sku_ids = redis_conn.lrange(request.user.id, 0, 4)
        # skus = SKU.objects.filter(id__in=sku_ids)
        sku_li = []
        for sku_id in sku_ids:
            sku = SKU.objects.get(id=sku_id)
            sku_li.append({
                "id": sku.id,
                "name": sku.name,
                "price": sku.price,
                "comments": sku.comments,
                "default_image_url": "http://192.168.19.131:8888/" + sku.default_image.name
            })
        return JsonResponse({"code": 0,
                             "message": "OK",
                             "skus": sku_li})
