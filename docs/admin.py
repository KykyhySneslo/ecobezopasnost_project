from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Document, DocumentCategory

@admin.register(DocumentCategory)
class DocumentCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'order', 'document_count')
    list_editable = ('order',)
    prepopulated_fields = {'slug': ('name',)}
    
    def document_count(self, obj):
        return obj.document_set.count()
    document_count.short_description = 'Кол-во документов'

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'file_type_display', 'file_size_display', 
                   'uploaded_at', 'download_count', 'is_published', 'preview_icon')
    list_filter = ('file_type', 'category', 'is_published', 'uploaded_at')
    search_fields = ('title', 'description')
    readonly_fields = ('file_type', 'file_size', 'uploaded_at', 'updated_at', 
                      'download_count', 'file_info')
    list_editable = ('is_published',)
    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'description', 'category', 'is_published')
        }),
        ('Файл', {
            'fields': ('file', 'file_info')
        }),
        ('Дополнительно', {
            'fields': ('uploaded_at', 'updated_at', 'download_count')
        }),
    )
    
    def file_type_display(self, obj):
        return obj.get_file_type_display()
    file_type_display.short_description = 'Тип'
    
    def file_size_display(self, obj):
        return obj.get_file_size_display()
    file_size_display.short_description = 'Размер'
    
    def preview_icon(self, obj):
        icon_class = obj.get_file_icon()
        color = {
            'pdf': 'text-danger',
            'doc': 'text-primary',
            'xls': 'text-success',
            'ppt': 'text-warning',
            'image': 'text-info',
            'other': 'text-secondary',
        }.get(obj.file_type, 'text-secondary')
        
        return format_html(
            '<i class="fas {} {} fa-2x"></i>',
            icon_class, color
        )
    preview_icon.short_description = ''
    
    def file_info(self, obj):
        if obj.file:
            return format_html(
                '<strong>Тип:</strong> {}<br>'
                '<strong>Размер:</strong> {}<br>'
                '<strong>Имя файла:</strong> {}<br>'
                '<a href="{}" target="_blank" class="button">Просмотреть</a>',
                obj.get_file_type_display(),
                obj.get_file_size_display(),
                obj.file.name.split('/')[-1],
                obj.file.url
            )
        return "Файл не загружен"
    file_info.short_description = 'Информация о файле'