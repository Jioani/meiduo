from itsdangerous import TimedJSONWebSignatureSerializer, BadData
from django.conf import settings


def generate_secret_openid(openid):
    serializer = TimedJSONWebSignatureSerializer(settings.SECRET_KEY,
                                                 expires_in=600)
    data = {"openid": openid}
    secret_openid = serializer.dumps(data).decode()
    return secret_openid


def check_secret_openid(serect_openid):
    serializer = TimedJSONWebSignatureSerializer(settings.SECRET_KEY)
    try:
        data = serializer.loads(serect_openid)
    except BadData as e:
        return None
    else:
        return data.get("openid")
