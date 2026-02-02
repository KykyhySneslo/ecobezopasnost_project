from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

class Conversation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_conversations')
    employee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='employee_conversations')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user_last_seen = models.DateTimeField(null=True, blank=True)
    employee_last_seen = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user} - {self.employee}"

    class Meta:
        ordering = ['-updated_at']


class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    file = models.FileField(upload_to='chat_files/', null=True, blank=True)
    file_name = models.CharField(max_length=255, null=True, blank=True)
    file_type = models.CharField(max_length=50, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def get_file_icon(self):
        if not self.file:
            return 'fa-file'
        ext = self.file.name.split('.')[-1].lower()
        if ext in ['jpg', 'jpeg', 'png', 'gif', 'bmp']:
            return 'fa-file-image'
        elif ext in ['pdf']:
            return 'fa-file-pdf'
        elif ext in ['doc', 'docx']:
            return 'fa-file-word'
        elif ext in ['xls', 'xlsx']:
            return 'fa-file-excel'
        elif ext in ['mp4', 'avi', 'mov']:
            return 'fa-file-video'
        else:
            return 'fa-file'

    def get_file_size_display(self):
        if not self.file:
            return ''
        size = self.file.size
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        else:
            return f"{size / (1024 * 1024):.1f} MB"

    def __str__(self):
        return f"{self.sender}: {self.text[:50]}"

    class Meta:
        ordering = ['timestamp']


class EmployeeStatus(models.Model):
    employee = models.OneToOneField(User, on_delete=models.CASCADE, related_name='employee_status')
    is_online = models.BooleanField(default=False)
    last_seen = models.DateTimeField(null=True, blank=True)

    def update_status(self, is_online):
        """Обновляет статус сотрудника"""
        self.is_online = is_online
        self.last_seen = timezone.now()
        self.save()

    @property
    def status_display(self):
        """Возвращает текстовое представление статуса"""
        if not self.last_seen:
            return "никогда не был(а) в сети"
        
        now = timezone.now()
        time_diff = now - self.last_seen
        
        if self.is_online:
            return "онлайн"
        elif time_diff < timedelta(minutes=2):
            return "был(а) только что"
        elif time_diff < timedelta(hours=1):
            minutes = int(time_diff.total_seconds() // 60)
            return f"был(а) {minutes} минут назад"
        elif time_diff < timedelta(days=1):
            hours = int(time_diff.total_seconds() // 3600)
            return f"был(а) {hours} часов назад"
        else:
            days = time_diff.days
            return f"был(а) {days} дней назад"

    @property
    def is_recently_active(self):
        """Проверяет, был ли сотрудник активен в последние 2 минуты"""
        if self.is_online:
            return True
        if self.last_seen:
            return (timezone.now() - self.last_seen) < timedelta(minutes=2)
        return False

    def __str__(self):
        return f"{self.employee} - {self.status_display}"

    class Meta:
        verbose_name = 'Статус сотрудника'
        verbose_name_plural = 'Статусы сотрудников'