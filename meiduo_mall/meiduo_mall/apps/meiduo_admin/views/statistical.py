from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser
from users.models import User


class UserDayActiveView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        now_date = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        count = User.objects.filter(last_login__gte=now_date).count()
        return Response({"count": count,
                         "date": now_date.date()})


class UserDayOrdersView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        now_date = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        count = User.objects.filter(orders__create_time__gte=now_date).distinct().count()
        return Response({"count": count,
                         "date": now_date.date()})


class UserMonthCountView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        now_date = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        begin_date = now_date - timezone.timedelta(days=29)
        current_date = begin_date
        month_li = []
        while current_date <= now_date:
            next_date = current_date + timezone.timedelta(days=1)
            count = User.objects.filter(date_joined__gte=current_date,
                                        date_joined__lt=next_date).count()
            month_li.append({
                "count": count,
                "date": current_date.date()
            })
            current_date = next_date
        return Response(month_li)
