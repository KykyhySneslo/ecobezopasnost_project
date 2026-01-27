from django.utils.deprecation import MiddlewareMixin
from django.utils import timezone
from .models import EmployeeStatus
from django.contrib.auth import get_user_model

User = get_user_model()

class OnlineStatusMiddleware(MiddlewareMixin):
    """Обновление статуса онлайн/оффлайн для сотрудников"""
    
    def process_request(self, request):
        if request.user.is_authenticated and request.user.is_employee:
            try:
                status, created = EmployeeStatus.objects.get_or_create(
                    employee=request.user
                )
                status.is_online = True
                status.last_seen = timezone.now()
                status.save()
            except:
                pass
    
    def process_response(self, request, response):
        return response