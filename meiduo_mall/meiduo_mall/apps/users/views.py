from django.http import JsonResponse
from django.shortcuts import render
from django.views import View
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