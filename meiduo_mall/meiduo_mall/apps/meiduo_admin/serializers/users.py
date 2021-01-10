from rest_framework import serializers
from users.models import User


class AdminAuthSerializer(serializers.ModelSerializer):
    token = serializers.CharField(label="JWT token", read_only=True)
    username = serializers.CharField(label="用户名")

    class Meta:
        model = User
        fields = ("id", "username", "password", "token")
        extra_kwargs = {
            "password": {
                "write_only": True
            }
        }

    def validate(self, attrs):
        username = attrs.get("username")
        password = attrs.get("password")
        try:
            user = User.objects.get(username=username, is_staff=True)
        except User.DoesNotExist:
            raise serializers.as_serializer_error("用户名或者密码错误")
        else:
            if not user.check_password(password):
                raise serializers.as_serializer_error("用户名或者密码错误")
            attrs["user"] = user
            return attrs

    def create(self, validated_data):
        username = validated_data["user"]
        user = User.objects.get(username=username)
        from rest_framework_jwt.settings import api_settings

        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

        payload = jwt_payload_handler(user)
        token = jwt_encode_handler(payload)
        user.token = token
        return user