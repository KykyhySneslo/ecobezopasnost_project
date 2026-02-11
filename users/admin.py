from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html  # <-- Импортируем format_html
from .models import CustomUser
from .forms import CustomUserCreationForm, CustomUserChangeForm

class CustomUserAdmin(UserAdmin):
    """Админка для кастомной модели пользователя"""
    
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = CustomUser
    
    # ---------- Отображение в списке пользователей ----------
    list_display = (
        'avatar_preview',        # Превью аватара
        'username', 'email', 
        'first_name', 'last_name', 
        'is_staff', 'is_employee', 
        'is_active', 'date_joined'
    )
    list_filter = ('is_employee', 'is_staff', 'is_superuser', 'is_active', 'groups')
    search_fields = ('username', 'first_name', 'last_name', 'email', 'phone_number')
    ordering = ('-date_joined',)
    
    # ---------- Поля только для чтения ----------
    readonly_fields = ('last_login', 'date_joined', 'avatar_preview_large')
    
    # ---------- Кастомные действия ----------
    actions = ['make_employee', 'remove_employee']
    
    # ---------- Настройка полей для формы редактирования существующего пользователя ----------
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Персональная информация'), {
            'fields': (
                'first_name', 'last_name', 'email', 'phone_number',
                'avatar', 'avatar_preview_large'   # превью под полем загрузки
            )
        }),
        (_('Права доступа'), {
            'fields': (
                'is_active', 'is_staff', 'is_superuser', 'is_employee',
                'groups', 'user_permissions'
            ),
        }),
        (_('Важные даты'), {
            'fields': ('last_login', 'date_joined')
        }),
    )
    
    # ---------- Настройка полей для формы создания нового пользователя ----------
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'username', 'email', 'first_name', 'last_name',
                'phone_number', 'password1', 'password2',
                'is_staff', 'is_employee', 'is_active'
            ),
        }),
    )
    
    # ---------- Кастомизация формы в зависимости от прав ----------
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if not request.user.is_superuser:
            if 'is_superuser' in form.base_fields:
                form.base_fields['is_superuser'].disabled = True
            if 'user_permissions' in form.base_fields:
                form.base_fields['user_permissions'].disabled = True
        return form
    
    # ---------- Методы для отображения аватара ----------
    def avatar_preview(self, obj):
        """Превью аватара в списке пользователей"""
        if obj.avatar:
            return format_html(
                '<img src="{}" width="30" height="30" style="border-radius: 50%; object-fit: cover;" />',
                obj.avatar.url
            )
        return "—"
    avatar_preview.short_description = 'Аватар'
    
    def avatar_preview_large(self, obj):
        """Превью аватара в детальном просмотре"""
        if obj.avatar:
            return format_html(
                '<img src="{}" width="150" height="150" style="border-radius: 50%; object-fit: cover;" />',
                obj.avatar.url
            )
        return "Аватар не установлен"
    avatar_preview_large.short_description = 'Превью аватара'
    
    # ---------- Действия с пользователями ----------
    def make_employee(self, request, queryset):
        updated = queryset.update(is_employee=True)
        self.message_user(request, f'{updated} пользователей назначены сотрудниками.')
    make_employee.short_description = "Назначить сотрудниками"
    
    def remove_employee(self, request, queryset):
        updated = queryset.update(is_employee=False)
        self.message_user(request, f'{updated} пользователей лишены статуса сотрудника.')
    remove_employee.short_description = "Убрать статус сотрудника"

# Регистрируем модель
admin.site.register(CustomUser, CustomUserAdmin)