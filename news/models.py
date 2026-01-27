from django.db import models
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

User = get_user_model()

class News(models.Model):
    title = models.CharField(max_length=200, verbose_name='Заголовок')
    short_description = models.TextField(max_length=500, verbose_name='Краткое описание')
    full_text = models.TextField(verbose_name='Полный текст')
    image = models.ImageField(upload_to='news_images/', blank=True, null=True, verbose_name='Изображение')
    attached_file = models.FileField(upload_to='news_files/', blank=True, null=True, verbose_name='Прикрепленный файл')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    is_published = models.BooleanField(default=True, verbose_name='Опубликовано')
    author = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name='Автор',
        limit_choices_to={'is_employee': True}  # Только сотрудники
    )
    
    class Meta:
        verbose_name = 'Новость'
        verbose_name_plural = 'Новости'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['is_published']),
        ]
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('news:detail', kwargs={'pk': self.pk})