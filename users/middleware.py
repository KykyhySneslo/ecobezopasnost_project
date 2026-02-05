from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages

class EmailVerificationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Исключаем страницы, которые доступны без подтверждения email
        excluded_paths = [
            reverse('users:logout'),
            reverse('users:verify_email'),
            reverse('users:resend_verification_code'),
            '/admin/',  # Админка
        ]
        
        # Проверяем только аутентифицированных пользователей
        if request.user.is_authenticated and not request.user.email_verified:
            # Проверяем, не находится ли пользователь на исключенной странице
            if not any(request.path.startswith(path) for path in excluded_paths):
                # Если пользователь еще не подтвердил email
                if request.path != reverse('users:verify_email'):
                    messages.warning(request, 'Пожалуйста, подтвердите ваш email для доступа к полному функционалу.')
                    return redirect('users:verify_email')
        
        response = self.get_response(request)
        return response