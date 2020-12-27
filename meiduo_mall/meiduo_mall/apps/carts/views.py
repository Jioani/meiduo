import base64

from django.http import JsonResponse
from django.shortcuts import render
from django.views import View
import json
import pickle
from django_redis import get_redis_connection

from goods.models import SKU


class CartView(View):
    def post(self, request):
        #获取请求数据
        req_data = json.loads(request.body)
        sku_id = req_data.get("sku_id")
        count = req_data.get("count")
        selected = req_data.get("selected", True)
        #数据校验
        if not all([sku_id, count]):
            return JsonResponse({"code": 400,
                                 "message": "参数不完整"})
        try:
            sku = SKU.objects.get(id=sku_id)
        except Exception as e:
            return JsonResponse({"code": 400,
                                 "message": "商品输入错误"})
        try:
            count = int(count)
        except Exception as e:
            return JsonResponse({"code": 400,
                                 "message": "数量输入错误"})
        if request.user.is_authenticated:
            try:
                redis_conn = get_redis_connection("cart")
                pl = redis_conn.pipeline()
                pl.hincrby("cart_%s" % request.user.id, sku_id, count)
                if selected:
                    pl.sadd("cart_selected_%s" % request.user.id, sku_id)
                pl.execute()
            except Exception as e:
                print(e)
                return JsonResponse({"code": 400,
                                     "message": "数据库操作失败"})
            return JsonResponse({"code": 0,
                                 "message": "OK",
                                 "count": count
                                 })
        else:
            cart = request.COOKIES.get("cart")
            if cart is not None:
                cart = pickle.loads(base64.b64decode(cart))
            else:
                cart = {}
            sku = cart.get(sku_id)
            if sku:
                count += int(sku.get("count"))
            cart[sku_id] = {"count": count,
                            "selected": selected}
            cookie_cart = base64.b64encode(pickle.dumps(cart)).decode()
            response = JsonResponse({"code": 0,
                                     "message": "OK",
                                     "count": count})
            response.set_cookie("cart", cookie_cart, max_age=3600 * 24 * 90)
            return response

    def get(self, request):
        if request.user.is_authenticated:
            redis_conn = get_redis_connection("cart")
            redis_cart = redis_conn.hgetall("cart_%s" % request.user.id)
            redis_selected = redis_conn.smembers("cart_selected_%s" % request.user.id)
            cart = {}
            for sku_id, count in redis_cart.items():
                cart[int(sku_id)] = {
                    "count": int(count),
                    "selected": sku_id in redis_selected
                }
        else:
            cart = request.COOKIES.get("cart")
            if cart:
                cart = pickle.loads(base64.b64decode(cart))
            else:
                cart = {}
        skus = SKU.objects.filter(id__in=cart.keys())
        skus_list = []
        for sku in skus:
            sku_dict = {
                "id": sku.id,
                "name": sku.name,
                "price": sku.price,
                "default_image_url": "http://192.168.19.131:8888/" + sku.default_image.name,
                "count": cart[sku.id]["count"],
                "selected": cart[sku.id]["selected"]
            }
            skus_list.append(sku_dict)
        return JsonResponse({"code": 0,
                             "message": "OK",
                             "cart_skus": skus_list})

    def put(self, request):
        req_data = json.loads(request.body)
        sku_id = req_data.get("sku_id")
        count = req_data.get("count")
        selected = req_data.get("selected", True)
        if not all([sku_id, count]):
            return JsonResponse({"code": 400,
                                 "message": "缺少必传参数"})
        try:
            sku = SKU.objects.get(id=sku_id)
        except Exception as e:
            return JsonResponse({"code": 400,
                                 "message": "查询数据库出错"})
        try:
            count = int(count)
        except Exception as e:
            return JsonResponse({"code": 400,
                                 "message": "数量参数错误"})
        if request.user.is_authenticated:
            try:
                redis_conn = get_redis_connection("cart")
                pl = redis_conn.pipeline()
                pl.hset("cart_%s" % request.user.id, sku_id, count)
                if not selected:
                    pl.srem("cart_selected_%s" % request.user.id, sku_id)
                pl.sadd("cart_selected_%s" % request.user.id, sku_id)
                pl.execute()
            except Exception as e:
                print(e)
                return JsonResponse({"code": 400,
                                     "message": "数据库操作有误"})
            return JsonResponse({"code": 0,
                                 "message": "OK",
                                 "cart_sku": {"sku_id": sku_id,
                                              "count": count,
                                              "selected": selected}})
        else:
            cart = request.COOKIES.get("cart")
            if cart is None:
                cart = {}
            else:
                cart = pickle.loads(base64.b64decode(cart))
            sku = cart.get(sku_id)
            # if sku:
            #     count += int(sku.get("count"))
            cart[sku_id] = {
                "count": count,
                "selected": selected
            }
            cookie_cart = base64.b64encode(pickle.dumps(cart)).decode()
            response = JsonResponse({"code": 0,
                                     "message": "OK",
                                     "cart_sku": {"sku_id": sku_id,
                                                  "count": count,
                                                  "selected": selected}})
            response.set_cookie("cart", cookie_cart, max_age=90*24*3600)
            return response

    def delete(self, request):
        req_data = json.loads(request.body)
        sku_id = req_data.get("sku_id")
        try:
            sku = SKU.objects.get(id=sku_id)
        except Exception as e:
            return JsonResponse({"code": 400,
                                 "message": "查询商品失败"})
        if request.user.is_authenticated:
            try:
                redis_conn = get_redis_connection("cart")
                pl = redis_conn.pipeline()
                pl.hdel("cart_%s" % request.user.id, sku_id)
                pl.srem("cart_selected_%s" % request.user.id, sku_id)
                pl.execute()
            except Exception as e:
                return JsonResponse({"code": 400,
                                     "message": "操作数据库出错"})
            return JsonResponse({"code": 0,
                                 "message": "购物车记录删除成功"})
        else:
            cart = request.COOKIES.get("cart")
            if cart is not None:
                cart = pickle.loads(base64.b64decode(cart))
                if sku_id in cart:
                    del cart[sku_id]
                    cookie_cart = base64.b64encode(pickle.dumps(cart)).decode()
                    response = JsonResponse({"code": 0,
                                             "message": "购物车记录删除成功"})
                    response.set_cookie("cart", cookie_cart, max_age=90*24*3600)
                    return response
                else:
                    return JsonResponse({"code": 400,
                                         "message": "购物车没有该商品"})
            else:
                return JsonResponse({"code": 400,
                                     "message": "购物车为空"})


class CartSelectView(View):
    def put(self, request):
        req_data = json.loads(request.body)
        selected = req_data.get("selected", True)
        if request.user.is_authenticated:
            redis_conn = get_redis_connection("cart")
            sku_ids = redis_conn.hkeys("cart_%s" % request.user.id)
            cart_selected_key = 'cart_selected_%s' % request.user.id
            for sku_id in sku_ids:
                if selected:
                    redis_conn.sadd(cart_selected_key, sku_id)
                else:
                    redis_conn.srem(cart_selected_key, sku_id)
            return JsonResponse({"code": 0,
                                 "message": "OK"})
        else:
            cart = request.COOKIES.get("cart")
            if not cart:
                return JsonResponse({"code": 0,
                                     "message": "OK"})
            cart_data = pickle.loads(base64.b64decode(cart))
            for sku_id in cart_data:
                cart_data[sku_id]["selected"] = selected
            response = JsonResponse({"code": 0,
                                     "message": "OK"})
            cart_cookie = base64.b64encode(pickle.dumps(cart_data)).decode()
            response.set_cookie("cart", cart_cookie, max_age=90*24*3600)
            return response


































        