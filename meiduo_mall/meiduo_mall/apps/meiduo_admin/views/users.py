from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import GenericAPIView, CreateAPIView
from meiduo_admin.serializers.users import AdminAuthSerializer
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
