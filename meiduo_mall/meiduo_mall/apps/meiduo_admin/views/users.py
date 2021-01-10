from rest_framework import status
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import GenericAPIView, CreateAPIView, ListAPIView
from meiduo_admin.serializers.users import AdminAuthSerializer, UserInfoSerializer
from users.models import User

"""
使用CreateAPIView压缩简写代码
"""


class AdminAuthorizeView(CreateAPIView):
    queryset = User.objects.all()
    serializer_class = AdminAuthSerializer

    # def post(self, request):
    #     serializer = self.serializer_class(data=request.data)
    #     serializer.is_valid(raise_exception=True)
    #     serializer.save()
    #     return Response(serializer.data, status=status.HTTP_201_CREATED)


class UserInfoView(ListAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = UserInfoSerializer

    # 重写 get_queryset 方法
    def get_queryset(self):
        keyword = self.request.query_params.get("keyword")
        if keyword:
            # 如果未传递 keyword，查询所有的普通用户数据
            users = User.objects.filter(is_staff=False, username__contains=keyword)
        else:
            # 如果传递了 keyword，查询用户名中含有 keyword 的普通用户数据
            users = User.objects.filter(is_staff=False)
        return users

    # def get(self, request):
    #     users = self.get_queryset()
    #     serializer = self.get_serializer(users, many=True)
    #     return Response(serializer.data)
















