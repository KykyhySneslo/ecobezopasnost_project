from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.conf import settings

User = get_user_model()

class Command(BaseCommand):
    help = 'Создание начальных пользователей для тестирования'

    def handle(self, *args, **options):
        # Создаем администратора
        admin, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@ecobezopasnost.ru',
                'first_name': 'Администратор',
                'last_name': 'Системы',
                'is_staff': True,
                'is_superuser': True,
                'is_employee': True,
                'is_active': True,
            }
        )
        if created:
            admin.set_password('admin123')
            admin.save()
            self.stdout.write(self.style.SUCCESS('Создан администратор: admin / admin123'))
        else:
            self.stdout.write(self.style.WARNING('Администратор уже существует'))

        # Создаем сотрудника поддержки
        support, created = User.objects.get_or_create(
            username='support',
            defaults={
                'email': 'support@ecobezopasnost.ru',
                'first_name': 'Мария',
                'last_name': 'Поддержкина',
                'is_staff': True,
                'is_employee': True,
                'is_active': True,
            }
        )
        if created:
            support.set_password('support123')
            support.save()
            self.stdout.write(self.style.SUCCESS('Создан сотрудник поддержки: support / support123'))
        else:
            self.stdout.write(self.style.WARNING('Сотрудник поддержки уже существует'))

        # Создаем тестового пользователя
        user, created = User.objects.get_or_create(
            username='user',
            defaults={
                'email': 'user@example.ru',
                'first_name': 'Иван',
                'last_name': 'Пользователев',
                'is_active': True,
            }
        )
        if created:
            user.set_password('user123')
            user.save()
            self.stdout.write(self.style.SUCCESS('Создан тестовый пользователь: user / user123'))
        else:
            self.stdout.write(self.style.WARNING('Тестовый пользователь уже существует'))

        # Выводим итоги
        self.stdout.write(self.style.SUCCESS('\nИтоги:'))
        self.stdout.write(f'Всего пользователей: {User.objects.count()}')
        self.stdout.write(f'Сотрудников: {User.objects.filter(is_employee=True).count()}')
        self.stdout.write(f'Администраторов: {User.objects.filter(is_superuser=True).count()}')
        
        self.stdout.write(self.style.SUCCESS('\nДанные для входа:'))
        self.stdout.write('1. Админка: admin / admin123')
        self.stdout.write('2. Сотрудник: support / support123')
        self.stdout.write('3. Пользователь: user / user123')