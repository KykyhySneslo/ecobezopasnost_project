from django.contrib import admin
from django.utils.html import format_html
from .models import News

@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'created_at', 'is_published', 'preview_image')
    list_filter = ('is_published', 'created_at', 'author')
    search_fields = ('title', 'short_description', 'full_text')
    readonly_fields = ('created_at', 'updated_at', 'preview_image_detailed')
    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'short_description', 'full_text')
        }),
        ('Медиа', {
            'fields': ('image', 'preview_image_detailed', 'attached_file')
        }),
        ('Дополнительно', {
            'fields': ('author', 'is_published', 'created_at', 'updated_at')
        }),
    )
    
    def preview_image(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" width="50" height="50" style="object-fit: cover;" />',
                obj.image.url
            )
        return "—"
    preview_image.short_description = 'Изображение'
    
    def preview_image_detailed(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" width="200" style="object-fit: cover; border-radius: 5px;" />',
                obj.image.url
            )
        return "Изображение не загружено"
    preview_image_detailed.short_description = 'Предпросмотр'
    
    def save_model(self, request, obj, form, change):
        if not obj.author:
            obj.author = request.user
        super().save_model(request, obj, form, change)