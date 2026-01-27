from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import CustomUser
from .forms import CustomUserCreationForm, CustomUserChangeForm

class CustomUserAdmin(UserAdmin):
    """Админка для кастомной модели пользователя"""
    # Добавляем превью аватара в список
    list_display = ('avatar_preview', 'username', 'email', 'first_name', 
                    'last_name', 'is_staff', 'is_employee', 'is_active')
    
    # Добавляем превью в детальную форму
    readonly_fields = ('avatar_preview_large', 'last_login', 'date_joined')
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Персональная информация'), {
            'fields': ('first_name', 'last_name', 'email', 'phone_number', 
                      'avatar', 'avatar_preview_large')
        }),
        (_('Права доступа'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'is_employee', 
                      'groups', 'user_permissions'),
        }),
        (_('Важные даты'), {
            'fields': ('last_login', 'date_joined')
        }),
    )
    
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
    
    # Формы для создания/редактирования
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = CustomUser
    
    # Отображаемые поля в списке
    list_display = ('username', 'email', 'first_name', 'last_name', 
                    'is_staff', 'is_employee', 'is_active', 'date_joined')
    list_filter = ('is_employee', 'is_staff', 'is_superuser', 'is_active', 'groups')
    search_fields = ('username', 'first_name', 'last_name', 'email', 'phone_number')
    
    # Порядок полей при редактировании
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Персональная информация'), {
            'fields': ('first_name', 'last_name', 'email', 'phone_number', 'avatar')
        }),
        (_('Права доступа'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'is_employee', 
                      'groups', 'user_permissions'),
        }),
        (_('Важные даты'), {
            'fields': ('last_login', 'date_joined')
        }),
    )
    
    # Порядок полей при создании
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'first_name', 'last_name', 
                      'phone_number', 'password1', 'password2', 
                      'is_staff', 'is_employee', 'is_active'),
        }),
    )
    
    # Порядок сортировки
    ordering = ('-date_joined',)
    
    # Действия в админке
    actions = ['make_employee', 'remove_employee']
    
    def make_employee(self, request, queryset):
        """Сделать выбранных пользователей сотрудниками"""
        updated = queryset.update(is_employee=True)
        self.message_user(request, f'{updated} пользователей назначены сотрудниками.')
    make_employee.short_description = "Назначить сотрудниками"
    
    def remove_employee(self, request, queryset):
        """Убрать статус сотрудника у выбранных пользователей"""
        updated = queryset.update(is_employee=False)
        self.message_user(request, f'{updated} пользователей лишены статуса сотрудника.')
    remove_employee.short_description = "Убрать статус сотрудника"
    
    # Отображение в админке
    readonly_fields = ('last_login', 'date_joined')
    
    def get_form(self, request, obj=None, **kwargs):
        """Кастомизация формы в зависимости от пользователя"""
        form = super().get_form(request, obj, **kwargs)
        
        # Для суперпользователя показываем все поля
        if not request.user.is_superuser:
            # Ограничиваем права для обычных сотрудников
            if 'is_superuser' in form.base_fields:
                form.base_fields['is_superuser'].disabled = True
            if 'user_permissions' in form.base_fields:
                form.base_fields['user_permissions'].disabled = True
        
        return form
    
    

# Регистрируем модель
admin.site.register(CustomUser, CustomUserAdmin)