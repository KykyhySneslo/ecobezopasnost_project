from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import os

User = get_user_model()

class Conversation(models.Model):
    """Диалог между пользователем и сотрудником"""
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='user_conversations',
        verbose_name='Пользователь'
    )
    employee = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='employee_conversations',
        limit_choices_to={'is_employee': True},
        verbose_name='Сотрудник'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    is_active = models.BooleanField(default=True, verbose_name='Активен')

    class Meta:
        verbose_name = 'Диалог'
        verbose_name_plural = 'Диалоги'
        ordering = ['-updated_at']
        unique_together = ['user', 'employee']  # Один диалог на пару

    def __str__(self):
        return f"{self.user} ↔ {self.employee}"

    def get_last_message(self):
        """Возвращает последнее сообщение в диалоге"""
        return self.messages.order_by('-timestamp').first()

class Message(models.Model):
    """Сообщение в диалоге"""
    conversation = models.ForeignKey(
        Conversation, 
        on_delete=models.CASCADE, 
        related_name='messages',
        verbose_name='Диалог'
    )
    sender = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        verbose_name='Отправитель'
    )
    text = models.TextField(blank=True, verbose_name='Текст сообщения')
    
    # Файлы
    file = models.FileField(
        upload_to='message_files/%Y/%m/%d/',
        blank=True, 
        null=True,
        verbose_name='Файл'
    )
    file_name = models.CharField(max_length=255, blank=True, verbose_name='Имя файла')
    file_type = models.CharField(max_length=50, blank=True, verbose_name='Тип файла')
    file_size = models.PositiveIntegerField(default=0, verbose_name='Размер файла')
    
    # Статусы
    timestamp = models.DateTimeField(default=timezone.now, verbose_name='Время отправки')
    is_read = models.BooleanField(default=False, verbose_name='Прочитано')
    
    class Meta:
        verbose_name = 'Сообщение'
        verbose_name_plural = 'Сообщения'
        ordering = ['timestamp']
        indexes = [
            models.Index(fields=['conversation', 'timestamp']),
            models.Index(fields=['sender']),
            models.Index(fields=['is_read']),
        ]

    def __str__(self):
        return f"{self.sender}: {self.text[:50]}"

    def save(self, *args, **kwargs):
        # Автоматически заполняем информацию о файле
        if self.file:
            if not self.file_name:
                self.file_name = os.path.basename(self.file.name)
            
            # Определяем тип файла
            ext = self.file.name.split('.')[-1].lower()
            if ext in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp']:
                self.file_type = 'image'
            elif ext in ['mp4', 'avi', 'mov', 'wmv', 'flv']:
                self.file_type = 'video'
            elif ext in ['pdf']:
                self.file_type = 'pdf'
            elif ext in ['doc', 'docx']:
                self.file_type = 'word'
            elif ext in ['xls', 'xlsx']:
                self.file_type = 'excel'
            else:
                self.file_type = 'other'
            
            # Получаем размер файла
            if not self.file_size:
                try:
                    self.file_size = self.file.size
                except:
                    self.file_size = 0
        
        super().save(*args, **kwargs)

    def get_file_icon(self):
        """Возвращает иконку для типа файла"""
        icons = {
            'image': 'fa-file-image',
            'video': 'fa-file-video',
            'pdf': 'fa-file-pdf',
            'word': 'fa-file-word',
            'excel': 'fa-file-excel',
            'other': 'fa-file',
        }
        return icons.get(self.file_type, 'fa-file')

    def get_file_size_display(self):
        """Возвращает размер файла в читаемом формате"""
        if self.file_size < 1024:
            return f"{self.file_size} Б"
        elif self.file_size < 1024 * 1024:
            return f"{self.file_size / 1024:.1f} КБ"
        else:
            return f"{self.file_size / (1024 * 1024):.1f} МБ"

class EmployeeStatus(models.Model):
    """Статус сотрудника (онлайн/оффлайн)"""
    employee = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={'is_employee': True},
        verbose_name='Сотрудник'
    )
    is_online = models.BooleanField(default=False, verbose_name='Онлайн')
    last_seen = models.DateTimeField(auto_now=True, verbose_name='Последний раз в сети')
    
    class Meta:
        verbose_name = 'Статус сотрудника'
        verbose_name_plural = 'Статусы сотрудников'

    def __str__(self):
        return f"{self.employee}: {'Онлайн' if self.is_online else 'Оффлайн'}"