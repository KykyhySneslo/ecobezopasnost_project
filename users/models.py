from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    # Расширяем стандартную модель
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True)
    is_employee = models.BooleanField(default=False)  # Флаг сотрудника
    
    def __str__(self):
        return self.username