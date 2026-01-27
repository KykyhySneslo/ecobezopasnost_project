from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Conversation, Message, EmployeeStatus

class MessageInline(admin.TabularInline):
    """Встроенное отображение сообщений в диалоге"""
    model = Message
    extra = 0
    readonly_fields = ('sender', 'text', 'file', 'timestamp', 'is_read')
    fields = ('sender', 'text', 'file_display', 'timestamp', 'is_read')
    ordering = ('-timestamp',)
    
    def file_display(self, obj):
        if obj.file:
            return format_html(
                '<a href="{}" target="_blank">{}</a>',
                obj.file.url,
                obj.file_name
            )
        return "—"
    file_display.short_description = 'Файл'
    
    def has_add_permission(self, request, obj=None):
        return False

@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    """Админка для диалогов"""
    list_display = ('id', 'user_link', 'employee_link', 'created_at', 
                    'updated_at', 'message_count', 'is_active')
    list_filter = ('is_active', 'created_at', 'employee')
    search_fields = ('user__username', 'user__email', 'user__first_name',
                    'user__last_name', 'employee__username')
    readonly_fields = ('created_at', 'updated_at')
    list_select_related = ('user', 'employee')
    inlines = [MessageInline]
    actions = ['activate_conversations', 'deactivate_conversations']
    
    def user_link(self, obj):
        url = reverse('admin:users_customuser_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = 'Пользователь'
    user_link.admin_order_field = 'user__username'
    
    def employee_link(self, obj):
        url = reverse('admin:users_customuser_change', args=[obj.employee.id])
        return format_html('<a href="{}">{}</a>', url, obj.employee.username)
    employee_link.short_description = 'Сотрудник'
    employee_link.admin_order_field = 'employee__username'
    
    def message_count(self, obj):
        return obj.messages.count()
    message_count.short_description = 'Сообщений'
    
    def activate_conversations(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, f'{queryset.count()} диалогов активировано.')
    activate_conversations.short_description = "Активировать диалоги"
    
    def deactivate_conversations(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f'{queryset.count()} диалогов деактивировано.')
    deactivate_conversations.short_description = "Деактивировать диалоги"

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    """Админка для сообщений"""
    list_display = ('id', 'conversation_link', 'sender_link', 'text_preview', 
                    'has_file', 'timestamp', 'is_read')
    list_filter = ('is_read', 'timestamp', 'sender__is_employee')
    search_fields = ('text', 'sender__username', 'conversation__user__username')
    readonly_fields = ('timestamp', 'file_preview')
    list_select_related = ('sender', 'conversation')
    
    def conversation_link(self, obj):
        url = reverse('admin:messenger_conversation_change', args=[obj.conversation.id])
        return format_html('<a href="{}">Диалог #{}</a>', url, obj.conversation.id)
    conversation_link.short_description = 'Диалог'
    
    def sender_link(self, obj):
        url = reverse('admin:users_customuser_change', args=[obj.sender.id])
        return format_html('<a href="{}">{}</a>', url, obj.sender.username)
    sender_link.short_description = 'Отправитель'
    
    def text_preview(self, obj):
        return obj.text[:50] + "..." if len(obj.text) > 50 else obj.text
    text_preview.short_description = 'Текст'
    
    def has_file(self, obj):
        return "✓" if obj.file else "—"
    has_file.short_description = 'Файл'
    
    def file_preview(self, obj):
        if obj.file:
            return format_html(
                '<a href="{}" target="_blank">{}</a><br>'
                '<small>Тип: {} | Размер: {}</small>',
                obj.file.url,
                obj.file_name,
                obj.get_file_type_display(),
                obj.get_file_size_display()
            )
        return "—"
    file_preview.short_description = 'Файл (превью)'

@admin.register(EmployeeStatus)
class EmployeeStatusAdmin(admin.ModelAdmin):
    """Админка для статусов сотрудников"""
    list_display = ('employee_link', 'is_online', 'last_seen', 'status_duration')
    list_filter = ('is_online', 'last_seen')
    readonly_fields = ('last_seen',)
    search_fields = ('employee__username', 'employee__email')
    
    def employee_link(self, obj):
        url = reverse('admin:users_customuser_change', args=[obj.employee.id])
        return format_html('<a href="{}">{}</a>', url, obj.employee.username)
    employee_link.short_description = 'Сотрудник'
    
    def status_duration(self, obj):
        from django.utils import timezone
        from django.utils.timesince import timesince
        
        if obj.is_online:
            return "Онлайн"
        elif obj.last_seen:
            return f"Был {timesince(obj.last_seen)} назад"
        return "Неизвестно"
    status_duration.short_description = 'Статус'