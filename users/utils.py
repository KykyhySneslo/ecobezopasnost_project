from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import random

def generate_verification_code():
    """Генерирует 6-значный код"""
    return ''.join(random.choices('0123456789', k=6))

def send_verification_email(user, code):
    """Отправляет email с кодом подтверждения"""
    subject = 'Код подтверждения для регистрации в АНО "ЭкоБезопасность"'
    
    # HTML сообщение
    html_message = render_to_string('users/email/verification_email.html', {
        'user': user,
        'code': code,
        'site_name': 'АНО "ЭкоБезопасность"',
    })
    
    # Текстовое сообщение
    plain_message = strip_tags(html_message)
    
    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Ошибка отправки email: {e}")
        return False