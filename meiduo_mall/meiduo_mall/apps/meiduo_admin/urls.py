from django.urls import re_path
from rest_framework.routers import SimpleRouter

from meiduo_admin.views import users, statistical, skus

urlpatterns = [
    # 进行 URL 配置
    re_path(r"^authorizations/$", users.AdminAuthorizeView.as_view()),
    re_path(r"^statistical/day_active/$", statistical.UserDayActiveView.as_view()),
    re_path(r"^statistical/day_orders/$", statistical.UserDayOrdersView.as_view()),
    re_path(r"^statistical/month_increment/$", statistical.UserMonthCountView.as_view()),
    re_path(r"^users/$", users.UserInfoView.as_view()),
    # re_path(r"^skus/images/$", skus.SKUImageViewSet.as_view({
    #     "get": "list",
    #     "post": "create"
    # })),
    # re_path(r"^skus/images/(?P<pk>\d+)/$", skus.SKUImageViewSet.as_view({
    #     "get": "retrieve",
    #     "put": "update",
    #     "delete": "destroy"
    # })),
    re_path(r"^skus/simple/$", skus.SKUSimpleView.as_view()),
]

router = SimpleRouter()
router.register("skus/images", skus.SKUImageViewSet, "image")
urlpatterns += router.urls
