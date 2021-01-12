import re

from django_redis import get_redis_connection
from rest_framework import serializers
from rest_framework.response import Response

from carts.utils import CartHelper
from users.models import User


class RegisterSerializer(serializers.ModelSerializer):
    username = serializers.CharField(label="用户名")
    password2 = serializers.CharField(label="确认密码", write_only=True)
    sms_code = serializers.IntegerField(label="短信验证码", write_only=True)
    allow = serializers.BooleanField(label="是否同意协议", write_only=True)

    class Meta:
        model = User
        fields = ("username", "password", "password2", "mobile", "sms_code",
                  "allow", "id", "email")
        extra_kwargs = {
            "password": {
                "write_only": True
            },
            "email": {
                "read_only": True
            }
        }

    def validate(self, attrs):
        username = attrs["username"]
        password = attrs["password"]
        mobile = attrs["mobile"]
        password2 = attrs["password2"]
        allow = attrs["allow"]
        sms_code = attrs["sms_code"]
        if not re.match(r'^[a-zA-Z0-9_-]{5,20}$', username):
            raise serializers.ValidationError("用户名格式不正确")

        if not re.match(r'^[a-zA-Z0-9]{8,20}$', password):
            raise serializers.ValidationError('password格式错误')

        if password != password2:
            raise serializers.ValidationError('两次密码不一致')

        if not re.match(r'^1[3-9]\d{9}$', mobile):
            raise serializers.ValidationError('手机号格式错误')

        if not allow:
            raise serializers.ValidationError('请同意协议!')

        # 短信验证码检验
        redis_conn = get_redis_connection('verify_code')
        sms_code_redis = redis_conn.get('sms_%s' % mobile)

        if not sms_code_redis:
            raise serializers.ValidationError('短信验证码过期')

        if sms_code != int(sms_code_redis):
            raise serializers.ValidationError('短信验证码错误')
        return attrs

    def create(self, validated_data):
        username = validated_data["username"]
        password = validated_data["password"]
        mobile = validated_data["mobile"]
        try:
            user = User.objects.create_user(username=username,
                                            password=password,
                                            mobile=mobile)
        except Exception as e:
            raise serializers.ValidationError('数据库保存错误')
        from django.contrib.auth import login
        login(self.context("request"), user)
        # ③ 返回响应
        response = Response({'code': 0,
                             'message': 'OK'})
        response.set_cookie("username", user.username, max_age=30 * 24 * 3600)
        cart_helper = CartHelper(self.context("request"), response)
        cart_helper.merge_cookie_cart_to_redis()
        return user
