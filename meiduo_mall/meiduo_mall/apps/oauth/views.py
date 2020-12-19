import json
import re

from QQLoginTool.QQtool import OAuthQQ
from django.contrib.auth import login
from django.http import JsonResponse
from django.shortcuts import render
from django.views import View
from django.conf import settings
from django_redis import get_redis_connection

from oauth.models import OAuthQQUser
from oauth.utils import generate_secret_openid, check_secret_openid
from users.models import User


class QQLoginView(View):
    def get(self, request):
        next = request.GET.get("next", "/")
        oauth = OAuthQQ(client_id=settings.QQ_CLIENT_ID,
                        client_secret=settings.QQ_CLIENT_SECRET,
                        redirect_uri=settings.QQ_REDIRECT_URI,
                        state=next)
        login_url = oauth.get_qq_url()
        return JsonResponse({"code": 0,
                             "message": "OK",
                             "login_url": login_url})


class QQUserView(View):
    def get(self, request):
        code = request.GET.get("code")
        oauth = OAuthQQ(client_id=settings.QQ_CLIENT_ID,
                        client_secret=settings.QQ_CLIENT_SECRET,
                        redirect_uri=settings.QQ_REDIRECT_URI)
        try:
            access_token = oauth.get_access_token(code)
            openid = oauth.get_open_id(access_token)
        except:
            return JsonResponse({"code": 400,
                                 "message": "登陆失败"})
        try:
            qq_user = OAuthQQUser.objects.get(openid=openid)
        except:
            secret_openid = generate_secret_openid(openid)
            return JsonResponse({"code": 300,
                                 "message": "OK",
                                 "secret_openid": secret_openid})
        else:
            user = qq_user.user
            login(request, user)
            response = JsonResponse({"code": 0,
                                     "message": "OK"})
            response.set_cookie("username", user.username, max_age=14 * 24 * 3600)
            return response

    def post(self, request):
        req_data = json.loads(request.body.decode())
        mobile = req_data.get("mobile")
        password = req_data.get("password")
        sms_code = req_data.get("sms_code")
        secret_openid = req_data.get("secret_openid")
        if not all([mobile, password, sms_code, secret_openid]):
            return JsonResponse({"code": 400,
                                 "message": "缺少必传参数"})
        if not re.match(r"^1[3-9]\d{9}$", mobile):
            return JsonResponse({'code': 400,
                                 'message': '请输入正确的手机号码'})
        if not re.match(r"^[0-9A-Za-z]{8,20}$", password):
            return JsonResponse({'code': 400,
                                 'message': '请输入8-20位的密码'})
        redis_conn = get_redis_connection("verify_code")
        sms_code_redis = redis_conn.get("sms_%s" % mobile)
        if not sms_code_redis:
            return JsonResponse({"code": 400,
                                 "message": "短信验证码已失效"})
        if sms_code_redis != sms_code:
            return JsonResponse({"code": 400,
                                 "message": "短信验证码错误"})
        openid = check_secret_openid(secret_openid)
        if not openid:
            return JsonResponse({'code': 400,
                                 'message': 'secret_openid有误'})
        try:
            user = User.objects.get(mobile=mobile)
        except:
            import base64
            username = base64.b64encode(mobile.encode()).decode()
            user = User.objects.create(mobile=mobile, username=username, password=password)
        else:
            if not user.check_password(password):
                return JsonResponse({"code": 400,
                                     "message": "登录密码错误"})
        try:
            OAuthQQUser.objects.create(openid=openid,
                                      user=user)
        except Exception as e:
            print(e)
            return JsonResponse({'code': 400,
                                 'message': '数据库操作失败'})
        login(request, user)
        response = JsonResponse({'code': 0,
                                 'message': 'OK'})
        # 设置cookie
        response.set_cookie('username', user.username,
                            max_age=3600 * 24 * 14)
        return response

