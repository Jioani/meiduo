from django.urls import re_path
from users import views


urlpatterns = [
    re_path(r"^usernames/(?P<username>[a-zA-Z0-9_-]{5,20})/count/$",
            views.UsernameCountView.as_view())
]
