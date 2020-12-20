from django.urls import re_path
from areas import views


urlpatterns = [
    re_path(r"^areas/$", views.ProvinceAreaView.as_view()),
    re_path(r"^areas/(?P<pk>\d+)/$", views.SubAreaView.as_view()),
]
