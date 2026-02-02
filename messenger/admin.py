from django.contrib import admin
from .models import Conversation, Message, EmployeeStatus

@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'employee', 'created_at', 'updated_at', 'user_last_seen', 'employee_last_seen']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['user__username', 'user__email', 'employee__username', 'employee__email']
    raw_id_fields = ['user', 'employee']
    date_hierarchy = 'created_at'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user', 'employee')

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'conversation', 'sender', 'text_preview', 'timestamp', 'is_read']
    list_filter = ['timestamp', 'is_read']
    search_fields = ['text', 'sender__username']
    raw_id_fields = ['conversation', 'sender']
    date_hierarchy = 'timestamp'
    
    def text_preview(self, obj):
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text
    text_preview.short_description = 'Текст'

@admin.register(EmployeeStatus)
class EmployeeStatusAdmin(admin.ModelAdmin):
    list_display = ['employee', 'is_online', 'last_seen']
    list_filter = ['is_online']
    search_fields = ['employee__username', 'employee__email']
    raw_id_fields = ['employee']