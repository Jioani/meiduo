from django.http import JsonResponse


def login_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:           #用户登录验证
            return JsonResponse({"code": 400,
                                 "message": "用户未登录"})
        else:
            return view_func(request, *args, **kwargs)
    return wrapper


class LoginRequiredMixin(object):
    @classmethod
    def as_view(cls, **int_kwargs):
        view = super().as_view(**int_kwargs)
        return login_required(view)

