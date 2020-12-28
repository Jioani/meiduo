import json
import re

from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.core.mail import send_mail
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.shortcuts import render
from django.views import View
from django_redis import get_redis_connection

from meiduo_mall.utils.mixins import LoginRequiredMixin

import areas
from carts.utils import CartHelper
from users.models import User, Address


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
        from django.contrib.auth import login
        login(request, user)
        # ③ 返回响应
        response = JsonResponse({'code': 0,
                                 'message': 'OK'})
        response.set_cookie("username", user.username, max_age=30 * 24 * 3600)
        cart_helper = CartHelper(request, response)
        cart_helper.merge_cookie_cart_to_redis()
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
        response = JsonResponse({"code": 0,
                                 "message": "登录成功"})
        if not remember:
            request.session.set_expiry(0)
            response.set_cookie("username", user.username)
            return response
        response.set_cookie("username", user.username, max_age=30 * 24 * 3600)
        cart_helper = CartHelper(request, response)
        cart_helper.merge_cookie_cart_to_redis()
        return response


class LogoutView(View):
    def delete(self, request):
        logout(request)
        response = JsonResponse({"code": 0,
                                 "message": "ok"})
        response.delete_cookie("username")
        return response


class UserInfoView(LoginRequiredMixin, View):
    def get(self, request):
        user = request.user
        info = {"username": user.username,
                "mobile": user.mobile,
                "email": user.email,
                "email_active": user.email_active}
        return JsonResponse({"code": 0,
                             "message": "OK",
                             "user": info})


class UserEmailView(LoginRequiredMixin, View):
    def put(self, request):
        req_data = json.loads(request.body)
        email = req_data.get("email")
        if not email:
            return JsonResponse({"code": 400,
                                 "message": "缺少email参数"})
        if not re.match(r"^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$", email):
            return JsonResponse({"code": 400,
                                 "message": "邮箱格式不正确"})
        user = request.user
        try:
            user.email = email
            user.save()
        except Exception as e:
            return JsonResponse({"code": 400,
                                 "message": "邮箱设置失败"})
        # from celery_tasks.email.tasks import send_verify_email
        # verify_url = "http://邮件验证地址"
        # send_verify_email.delay(email, verify_url)
        verify_url = user.generate_verify_email_url()
        subject = "美多商城邮箱验证"
        html_message = '<p>尊敬的用户您好！</p>' \
                       '<p>感谢您使用美多商城</p>' \
                       '<p>您的邮箱为: %s 。请点击此链接激活您的邮箱：</p>' \
                       '<p><a href="%s">%s<a></p>' % (email, verify_url, verify_url)
        send_mail(subject, '', settings.EMAIL_FROM, [email], html_message=html_message)
        return JsonResponse({"code": 0,
                             "message": "OK"})


class EmailVerifyView(View):
    def put(self, request):
        token = request.GET.get("token")
        if not token:
            return JsonResponse({"code": 400,
                                 "message": "缺少token参数"})
        user = User.check_verify_email_token(token)
        if user is None:
            return JsonResponse({"code": 400,
                                 "message": "传入token信息有误"})
        try:
            user.email_active = True
            user.save()
        except Exception as e:
            return JsonResponse({"code": 400,
                                 "message": "邮箱验证失败"})
        return JsonResponse({"code": 0,
                             "message": "OK"})


class AddressView(LoginRequiredMixin, View):
    def post(self, request):
        try:
            count = Address.objects.filter(user=request.user, is_delete=False).count()
        except Exception:
            return JsonResponse({"code": 400,
                                 "message": "获取地址数据出错"})
        if count >= 20:
            return JsonResponse({"code": 400,
                                 "message": "收货地址超过上限"})
        req_data = json.loads(request.body)
        title = req_data.get("title")
        receiver = req_data.get('receiver')
        province_id = req_data.get('province_id')
        city_id = req_data.get('city_id')
        district_id = req_data.get('district_id')
        place = req_data.get('place')
        mobile = req_data.get('mobile')
        phone = req_data.get('phone')
        email = req_data.get('email')

        if not all([title, receiver, province_id, city_id, district_id, place, mobile]):
            return JsonResponse({"code": 400,
                                 "message": "缺少必传参数"})
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return JsonResponse({"code": 400,
                                 "message": "手机号不正确"})
        if phone:
            if not re.match(r'^(0[0-9]{2,3}-)?([2-9][0-9]{6,7})+(-[0-9]{1,4})?$', phone):
                return JsonResponse({'code': 400,
                                     'message': '参数phone有误'})
        if email:
            if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
                return JsonResponse({'code': 400,
                                     'message': '参数email有误'})
        try:
            address = Address.objects.create(user=request.user, **req_data)
            if not request.user.default_address:
                request.user.default_address = address
                request.user.save()
        except Exception:
            return JsonResponse({"code": 400,
                                 "message": "新增地址保存失败"})
        address_data = {
            'id': address.id,
            'title': address.title,
            'receiver': address.receiver,
            'province': address.province.name,
            'city': address.city.name,
            'district': address.district.name,
            'place': address.place,
            'mobile': address.mobile,
            'phone': address.phone,
            'email': address.email
        }
        return JsonResponse({'code': 0,
                             'message': 'OK',
                             'address': address_data})

    def get(self, request):
        try:
            address = Address.objects.filter(user=request.user, is_delete=False)
            address_list = []
            for address_data in address:
                address_dict = {"id": address_data.id,
                                "title": address_data.title,
                                "receiver": address_data.receiver,
                                "province": address_data.province.name,
                                "city": address_data.city.name,
                                "district": address_data.district.name,
                                "province_id": address_data.province_id,
                                "city_id": address_data.city_id,
                                "district_id": address_data.district_id,
                                "place": address_data.place,
                                "mobile": address_data.mobile,
                                "phone": address_data.phone,
                                "email": address_data.email}
                address_list.append(address_dict)
        except Exception as e:
            return JsonResponse({"code": 400,
                                 "message": "数据库操作出错"})
        return JsonResponse({"code": 0,
                             "message": "OK",
                             "default_address_id": request.user.default_address_id,
                             "addresses": address_list})


# API: PUT /addresses/(?P<address_id>\d+)/
class UpdateAddressView(LoginRequiredMixin, View):
    def put(self, request, address_id):
        req_data = json.loads(request.body)
        title = req_data.get("title")
        receiver = req_data.get('receiver')
        province_id = req_data.get('province_id')
        city_id = req_data.get('city_id')
        district_id = req_data.get('district_id')
        place = req_data.get('place')
        mobile = req_data.get('mobile')
        phone = req_data.get('phone')
        email = req_data.get('email')
        if not all([title, receiver, province_id, city_id, district_id, place, mobile]):
            return JsonResponse({"code": 400,
                                 "message": "缺少必传参数"})
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return JsonResponse({"code": 400,
                                 "message": "手机号不正确"})
        if phone:
            if not re.match(r'^(0[0-9]{2,3}-)?([2-9][0-9]{6,7})+(-[0-9]{1,4})?$', phone):
                return JsonResponse({'code': 400,
                                     'message': '参数phone有误'})
        if email:
            if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
                return JsonResponse({'code': 400,
                                     'message': '参数email有误'})
        try:
            address = Address.objects.filter(user=request.user, id=address_id).update(title=title,
                                                                                      receiver=receiver,
                                                                                      province_id=province_id,
                                                                                      city_id=city_id,
                                                                                      district_id=district_id,
                                                                                      place=place,
                                                                                      mobile=mobile,
                                                                                      phone=phone,
                                                                                      email=email)
            address = Address.objects.get(user=request.user, id=address_id)
            address_dict = {"id": address.id,
                            "title": address.title,
                            "receiver": address.receiver,
                            "province": address.province.name,
                            "city": address.city.name,
                            "district": address.district.name,
                            "province_id": address.province_id,
                            "city_id": address.city_id,
                            "district_id": address.district_id,
                            "place": address.place,
                            "mobile": address.mobile,
                            "phone": address.phone,
                            "email": address.email}
        except Exception as e:
            print(e)
            return JsonResponse({"code": 400,
                                 "message": "操作数据库出错"})
        return JsonResponse({"code": 0,
                             "message": "OK",
                             "address": address_dict})

    def delete(self, request, address_id):
        try:
            address = Address.objects.filter(user=request.user, id=address_id).update(is_delete=True)
        except:
            return JsonResponse({"code": 400,
                                 "message": "操作数据库出错"})
        return JsonResponse({"code": 0,
                             "message": "OK"})


class DefaultAddressView(LoginRequiredMixin, View):
    def put(self, request, address_id):
        try:
            user = User.objects.filter(id=request.user.id).update(default_address_id=address_id)
            # user = request.user
            # user.default_address_id = address_id
            # user.save()
        except Exception as e:
            return JsonResponse({"code": 400,
                                 "message": "操作数据库出错"})
        return JsonResponse({"code": 0,
                             "message": "OK"})


class UpdateAddressTitleView(LoginRequiredMixin, View):
    def put(self, request, address_id):
        req_data = json.loads(request.body)
        title = req_data.get("title")
        try:
            address = Address.objects.filter(user=request.user, id=address_id).update(title=title)
        except:
            return JsonResponse({"code": 400,
                                 "message": "操作数据库出错"})
        return JsonResponse({"code": 0,
                             "message": "OK"})


class UpdatePasswordView(LoginRequiredMixin, View):
    def put(self, request):
        req_data = json.loads(request.body)
        old_password = req_data.get("old_password")
        new_password = req_data.get("new_password")
        new_password2 = req_data.get("new_password2")
        try:
            user = request.user
        except Exception as e:
            return JsonResponse({"code": 400,
                                 "message": "操作数据库错误"})
        if not user.check_password(old_password):
            return JsonResponse({"code": 400,
                                 "message": "旧密码输入错误"})
        if not re.match(r'^[a-zA-Z0-9]{8,20}$', new_password):
            return JsonResponse({'code': 400,
                                 'message': 'password格式错误'})

        if new_password != new_password2:
            return JsonResponse({'code': 400,
                                 'message': '两次密码不一致'})
        try:
            user.set_password(new_password)
            user.save()
        except Exception as e:
            return JsonResponse({"code": 400,
                                 "message": "操作数据库出错"})
        return JsonResponse({"code": 0,
                             "message": "OK"})
