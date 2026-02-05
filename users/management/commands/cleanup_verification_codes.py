from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from users.models import EmailVerification

class Command(BaseCommand):
    help = 'Удаляет старые неподтвержденные коды верификации'

    def handle(self, *args, **kwargs):
        # Удаляем коды старше 24 часов
        cutoff_time = timezone.now() - timedelta(hours=24)
        deleted_count, _ = EmailVerification.objects.filter(
            created_at__lt=cutoff_time,
            is_verified=False
        ).delete()
        
        self.stdout.write(
            self.style.SUCCESS(f'Удалено {deleted_count} старых кодов верификации')
        )