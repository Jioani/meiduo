import json
from decimal import Decimal

from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views import View
from meiduo_mall.utils.mixins import LoginRequiredMixin

from carts.utils import CartHelper
from goods.models import SKU
from orders.models import OrderInfo, OrderGoods
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


class OrderCommitView(LoginRequiredMixin, View):
    def post(self, request):
        req_data = json.loads(request.body)
        address_id = req_data.get("address_id")
        pay_method = req_data.get("pay_method")
        if not all([address_id, pay_method]):
            return JsonResponse({"code": 400,
                                 "message": "缺少必传参数"})
        try:
            address = Address.objects.get(id=address_id)
        except Exception as e:
            return JsonResponse({"code": 400,
                                 "message": "地址信息有误"})
        if pay_method not in [1, 2]:
            return JsonResponse({"code": 400,
                                 "message": "支付方式有误"})
        user = request.user
        order_id = timezone.now().strftime("%Y%m%d%H%M%S") + "%09d" % user.id
        total_count = 0
        total_amount = 0
        if pay_method == 1:
            status = 2
        else:
            status = 1
        freight = Decimal(10.00)
        # 开启事务
        with transaction.atomic():
            # 设置数据库操作时, 事务中的保存点
            sid = transaction.savepoint()
            order = OrderInfo.objects.create(order_id=order_id,
                                             user=user,
                                             address=address,
                                             total_count=total_count,
                                             total_amount=total_amount,
                                             freight=freight,
                                             pay_method=pay_method,
                                             status=status)
            cart_helper = CartHelper(request)
            cart_dict = cart_helper.get_redis_selected_cart()
            sku_ids = cart_dict.keys()
            for sku_id in sku_ids:
                sku = SKU.objects.get(id=sku_id)
                count = cart_dict[sku_id]
                if count > sku.stock:
                    # 数据库操作时，撤销事务中指定保存点之后的操作
                    transaction.savepoint_commit(sid)
                    return JsonResponse({"code": 400,
                                         "message": "商品库存不足"})
                sku.stock -= count
                sku.sales += count
                sku.save()
                sku.spu.sales += count
                sku.spu.save()
                OrderGoods.objects.create(order=order,
                                          sku=sku,
                                          count=count,
                                          price=sku.price)
                total_amount += freight
                order.total_count = total_count
                order.total_amount = total_amount
                order.save()
                cart_helper.clear_redis_selected_cart()
                return JsonResponse({"code": 0,
                                     "message": "下单成功",
                                     "order_id": order_id})
