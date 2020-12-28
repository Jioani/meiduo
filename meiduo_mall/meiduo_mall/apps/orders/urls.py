from django.urls import re_path
from orders import views


urlpatterns = [
    re_path(r"^orders/settlement/$", views.OrderSettlementView.as_view()),
]
