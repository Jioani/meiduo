from django.urls import re_path
from meiduo_admin.views import users

urlpatterns = [
    # 进行 URL 配置
    re_path(r"^authorizations/$", users.AdminAuthorizeView.as_view()),
]
