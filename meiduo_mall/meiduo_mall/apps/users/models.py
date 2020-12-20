from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from itsdangerous import TimedJSONWebSignatureSerializer, BadData


# Create your models here.


class User(AbstractUser):
    mobile = models.CharField(max_length=11, unique=True, verbose_name="手机号")
    email_active = models.BooleanField(default=False, verbose_name="邮箱激活状态")

    class Meta:
        db_table = "tb_users"
        verbose_name = "用户"

    def generate_verify_email_url(self):
        serializer = TimedJSONWebSignatureSerializer(settings.SECRET_KEY, 7200)
        data = {"user_id": self.id,
                "email": self.email}
        token = serializer.dumps(data).decode()
        verify_url = settings.EMAIL_VERIFY_URL + token
        return verify_url

    @staticmethod
    def check_verify_email_token(token):
        serializer = TimedJSONWebSignatureSerializer(settings.SECRET_KEY)
        try:
            data = serializer.loads(token)
        except BadData as e:
            return None
        else:
            user_id = data.get("user_id")
            email = data.get("email")
        try:
            user = User.objects.get(id=user_id, email=email)
        except:
            return None
        else:
            return user
