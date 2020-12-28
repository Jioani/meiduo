from decimal import Decimal

from django.http import JsonResponse
from django.shortcuts import render
from django.views import View
from meiduo_mall.utils.mixins import LoginRequiredMixin

from carts.utils import CartHelper
from goods.models import SKU
from users.models import Address


class OrderSettlementView(LoginRequiredMixin, View):
    def get(self, request):
        """订单结算页面"""
        # ① 获取当前用户的收货地址信息
        addresses = Address.objects.filter(user=request.user, is_delete=False)
        # ② 从redis中获取用户所要结算的商品信息
        try:
            cart_helper = CartHelper(request)
            cart_data = cart_helper.get_redis_selected_cart()
        except Exception as e:
            return JsonResponse({"code": 400,
                                 "message": "获取购物车数据失败"})
        # ③ 查询数据库获取对应的商品数据
        # 商品数据
        sku_li = []
        try:
            skus = SKU.objects.filter(id__in=cart_data.keys())
            for sku in skus:
                sku_li.append({
                    "id": sku.id,
                    "name": sku.name,
                    "default_image_url": "http://192.168.19.131:8888/" + sku.default_image.name,
                    "price": sku.price,
                    "count": cart_data[sku.id]
                })
        except Exception as e:
            return JsonResponse({"code": 400,
                                 "message": "获取商品数据失败"})
        freight = Decimal(10.00)
        address_li = []
        try:
            for address in addresses:
                address_li.append({
                    "id": address.id,
                    "province": address.province.name,
                    "city": address.city.name,
                    "district": address.district.name,
                    "place": address.place,
                    "receiver": address.receiver,
                    "mobile": address.mobile
                })
        except Exception as e:
            return JsonResponse({"code": 400,
                                 "message": "地址信息获取错误"})
        context = {
            "addresses": address_li,
            "skus": sku_li,
            "freight": freight,
            "nowsite": request.user.default_address_id
        }
        return JsonResponse({"code": 0,
                             "message": "OK",
                             "context": context})

