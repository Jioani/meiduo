import json
import re

from django.contrib.auth import authenticate, login
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.shortcuts import render
from django.views import View
from django_redis import get_redis_connection

from users.models import User
# Create your views here.


# GET /usernames/(?P<username>[a-zA-Z0-9_-]{5,20})/count/
class UsernameCountView(View):
    def get(self, request, username):
        try:
            count = User.objects.filter(username=username).count()
        except:
            return JsonResponse({"code": 400,
                                 "message": "数据库操作失败"})
        return JsonResponse({"code": 0,
                             "message": "OK",
                             "count": count})


class MobileCountView(View):
    def get(self, request, mobile):
        try:
            count = User.objects.filter(mobile=mobile).count()
        except:
            return JsonResponse({"code": 400,
                                 "message": "数据库操作失败"})
        return JsonResponse({"code": 0,
                             "message": "OK",
                             "count": count})


class RegisterView(View):
    def post(self, request):
        """注册用户信息保存"""
        # ① 获取参数并进行校验
        req_data = json.loads(request.body.decode())
        username = req_data.get('username')
        password = req_data.get('password')
        password2 = req_data.get('password2')
        mobile = req_data.get('mobile')
        allow = req_data.get('allow')
        sms_code = req_data.get('sms_code')

        if not all([username, password, password2, mobile, allow, sms_code]):
            return JsonResponse({'code': 400,
                                 'message': '缺少必传参数'})

        if not re.match(r'^[a-zA-Z0-9_-]{5,20}$', username):
            return JsonResponse({'code': 400,
                                 'message': 'username格式错误'})

        if not re.match(r'^[a-zA-Z0-9]{8,20}$', password):
            return JsonResponse({'code': 400,
                                 'message': 'password格式错误'})

        if password != password2:
            return JsonResponse({'code': 400,
                                 'message': '两次密码不一致'})

        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return JsonResponse({'code': 400,
                                 'message': '手机号格式错误'})

        if not allow:
            return JsonResponse({'code': 400,
                                 'message': '请同意协议!'})

        # 短信验证码检验
        redis_conn = get_redis_connection('verify_code')
        sms_code_redis = redis_conn.get('sms_%s' % mobile)

        if not sms_code_redis:
            return JsonResponse({'code': 400,
                                 'message': '短信验证码过期'})

        if sms_code != sms_code_redis:
            return JsonResponse({'code': 400,
                                 'message': '短信验证码错误'})

        # ② 保存新增用户数据到数据库
        try:
            user = User.objects.create_user(username=username,
                                            password=password,
                                            mobile=mobile)
        except Exception as e:
            return JsonResponse({'code': 400,
                                 'message': '数据库保存错误'})
        # ③ 返回响应
        response = JsonResponse({'code': 0,
                                 'message': 'OK'})
        response.set_cookie("username", user.username, max_age=30 * 24 * 3600)
        return response


class CSRFTokenView(View):
    def get(self, request):
        """获取csrf_token的值"""
        # ① 生成csrf_token的值
        csrf_token = get_token(request)

        # ② 将csrf_token的值返回
        return JsonResponse({'code': 0,
                             'message': 'OK',
                             'csrf_token': csrf_token})


class LoginView(View):
    def post(self, request):
        requ_data = json.loads(request.body)
        username = requ_data.get("username")
        password = requ_data.get("password")
        remember = requ_data.get("remember")
        if not all([username, password]):
            return JsonResponse({"code": 400,
                                 "message": "缺少必传参数"})
        if re.match("^1[3-9]\d{9}$", username):
            User.USERNAME_FIELD = "mobile"
        else:
            User.USERNAME_FIELD = "username"
        user = authenticate(username=username, password=password)
        if user is None:
            return JsonResponse({"code": "400",
                                 "message": "账号用户名或密码错误"})
        login(request, user)
        if not remember:
            request.session.set_expiry(0)
        response = JsonResponse({"code": 0,
                                 "message": "登录成功"})
        response.set_cookie("username", user.username, max_age=30 * 24 * 3600)
        return response
