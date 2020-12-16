from django.http import HttpResponse
from django.shortcuts import render
from django.views import View
from meiduo_mall.libs.captcha.captcha import captcha
# Create your views here.


# GET /image_codes/(?P<uuid>[\w-]+)/



class ImageCodeView(View):
    def get(self, request, uuid):
        text, image = captcha.generate_captcha()
        return HttpResponse(image, content_type="image/jpeg")
