# create_status_for_all.py
import os
import django
from django.utils import timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecobezopasnost.settings')
django.setup()

from django.contrib.auth import get_user_model
from messenger.models import EmployeeStatus

User = get_user_model()

# Создаем статусы для ВСЕХ пользователей
users = User.objects.all()
for user in users:
    status, created = EmployeeStatus.objects.get_or_create(
        employee=user,
        defaults={'is_online': False, 'last_seen': timezone.now()}
    )
    if created:
        print(f"✓ Создан статус для: {user.username} ({'сотрудник' if user.is_employee else 'пользователь'})")
    else:
        print(f"✓ Статус уже существует для: {user.username}")

print(f"\nГотово! Обработано {users.count()} пользователей.")