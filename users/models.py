from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from datetime import timedelta
import random
import string
class CustomUser(AbstractUser):
    # Расширяем стандартную модель
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True)
    is_employee = models.BooleanField(default=False)  # Флаг сотрудника
    email_verified = models.BooleanField(default=False, verbose_name='Email подтвержден')
    verification_code_sent_at = models.DateTimeField(null=True, blank=True)
     
    def can_request_verification(self):
        """Можно ли запросить новый код (не чаще чем раз в 2 минуты)"""
        if not self.verification_code_sent_at:
            return True
        return timezone.now() > self.verification_code_sent_at + timedelta(minutes=2)
    def __str__(self):
        return self.username
class EmailVerification(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)

    def is_expired(self):
        """Проверяет, истек ли срок действия кода (15 минут)"""
        return timezone.now() > self.created_at + timedelta(minutes=15)
    
    def __str__(self):
        return f"{self.user.email} - {self.code}"

    class Meta:
        verbose_name = 'Верификация email'
        verbose_name_plural = 'Верификации email'