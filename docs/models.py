from django.db import models
from django.utils import timezone
from django.core.validators import FileExtensionValidator

class DocumentCategory(models.Model):
    """Категория для документов"""
    name = models.CharField(max_length=100, verbose_name='Название категории')
    slug = models.SlugField(max_length=100, unique=True, verbose_name='URL-адрес')
    description = models.TextField(blank=True, verbose_name='Описание')
    order = models.PositiveIntegerField(default=0, verbose_name='Порядок')
    
    class Meta:
        verbose_name = 'Категория документов'
        verbose_name_plural = 'Категории документов'
        ordering = ['order', 'name']
    
    def __str__(self):
        return self.name

class Document(models.Model):
    DOCUMENT_TYPES = [
        ('pdf', 'PDF'),
        ('doc', 'Word'),
        ('xls', 'Excel'),
        ('ppt', 'PowerPoint'),
        ('image', 'Изображение'),
        ('other', 'Другое'),
    ]
    
    title = models.CharField(max_length=200, verbose_name='Название документа')
    description = models.TextField(blank=True, verbose_name='Описание')
    file = models.FileField(
        upload_to='documents/%Y/%m/',
        verbose_name='Файл',
        validators=[
            FileExtensionValidator(['pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'jpg', 'jpeg', 'png'])
        ]
    )
    file_type = models.CharField(max_length=10, choices=DOCUMENT_TYPES, default='other', verbose_name='Тип файла')
    file_size = models.PositiveIntegerField(editable=False, default=0, verbose_name='Размер файла (байт)')
    category = models.ForeignKey(
        DocumentCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Категория'
    )
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата загрузки')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')
    is_published = models.BooleanField(default=True, verbose_name='Опубликовано')
    download_count = models.PositiveIntegerField(default=0, editable=False, verbose_name='Количество скачиваний')
    
    class Meta:
        verbose_name = 'Документ'
        verbose_name_plural = 'Документы'
        ordering = ['title']
        indexes = [
            models.Index(fields=['title']),
            models.Index(fields=['file_type']),
            models.Index(fields=['uploaded_at']),
        ]
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        # Автоматически определяем тип файла по расширению
        if self.file:
            ext = self.file.name.split('.')[-1].lower()
            if ext in ['pdf']:
                self.file_type = 'pdf'
            elif ext in ['doc', 'docx']:
                self.file_type = 'doc'
            elif ext in ['xls', 'xlsx']:
                self.file_type = 'xls'
            elif ext in ['ppt', 'pptx']:
                self.file_type = 'ppt'
            elif ext in ['jpg', 'jpeg', 'png', 'gif', 'bmp']:
                self.file_type = 'image'
            else:
                self.file_type = 'other'
            
            # Сохраняем размер файла
            self.file_size = self.file.size
        
        super().save(*args, **kwargs)
    
    def get_file_icon(self):
        """Возвращает класс иконки для типа файла"""
        icons = {
            'pdf': 'fa-file-pdf',
            'doc': 'fa-file-word',
            'xls': 'fa-file-excel',
            'ppt': 'fa-file-powerpoint',
            'image': 'fa-file-image',
            'other': 'fa-file',
        }
        return icons.get(self.file_type, 'fa-file')
    
    def get_file_size_display(self):
        """Возвращает размер файла в удобном формате"""
        if self.file_size < 1024:
            return f"{self.file_size} Б"
        elif self.file_size < 1024 * 1024:
            return f"{self.file_size / 1024:.1f} КБ"
        else:
            return f"{self.file_size / (1024 * 1024):.1f} МБ"