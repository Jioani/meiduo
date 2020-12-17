import random

from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views import View
from django_redis import get_redis_connection
from meiduo_mall.libs.captcha.captcha import captcha
# Create your views here.

import logging

from meiduo_mall.libs.yuntongxun.ccp_sms import CCP

logger = logging.getLogger("django")


# GET /image_codes/(?P<uuid>[\w-]+)/
class ImageCodeView(View):
    def get(self, request, uuid):
        text, image = captcha.generate_captcha()
        redis_conn = get_redis_connection("verify_code")
        redis_conn.set("img_%s" % uuid, text, 300)
        return HttpResponse(image, content_type="image/jpeg")


# GET /sms_codes/(?P<mobile>1[3-9]\d{9})/
class SMSCodeView(View):
    def get(self, request, mobile):
        redis_conn = get_redis_connection("verify_code")
        send_flag = redis_conn.get("send_flag_%s" % mobile)
        if send_flag:
            return JsonResponse({"code": 400,
                                 "message": "获取验证码频繁"})
        image_code = request.GET.get("image_code")
        uuid = request.GET.get("image_code_id")
        if not all([image_code, uuid]):
            return JsonResponse({"code": 400,
                                 "message": "缺少必传参数"})
        image_code_redis = redis_conn.get("img_%s" % uuid)
        if image_code_redis is None:
            return JsonResponse({"code": 400,
                                 "message": "图形验证码失效"})
        try:
            redis_conn.delete("img_%s" % uuid)
        except Exception as e:
            logger.error(e)
        if image_code.lower() != image_code_redis.lower():
            return JsonResponse({"code": 400,
                                 "message": "验证码输入错误"})
        sms_code = "%06d" % random.randint(0, 999999)
        logger.info("短信验证码为: %s" % sms_code)
        # redis_conn.set("sms_%s" % mobile, sms_code, 300)
        # redis_conn.set("send_flag_%s" % mobile, 1, 60)
        pl = redis_conn.pipeline()
        pl.set("sms_%s" % mobile, sms_code, 300)
        pl.set("send_flag_%s" % mobile, 1, 60)
        pl.execute()
        CCP().send_template_sms(mobile, [sms_code, 5], 1)
        return JsonResponse({"code": 0,
                             "message": "发送短信成功"})