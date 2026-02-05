from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, AuthenticationForm
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.utils import timezone
from datetime import timedelta
from .models import User, EmailVerification
import random

User = get_user_model()

class CustomUserCreationForm(UserCreationForm):
    """Форма для создания пользователя в админке"""
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 
                  'phone_number', 'is_staff', 'is_employee', 'is_active')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'vTextField'}),
            'email': forms.EmailInput(attrs={'class': 'vTextField'}),
            'first_name': forms.TextInput(attrs={'class': 'vTextField'}),
            'last_name': forms.TextInput(attrs={'class': 'vTextField'}),
            'phone_number': forms.TextInput(attrs={'class': 'vTextField'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Делаем пароль обязательным
        self.fields['password1'].required = True
        self.fields['password2'].required = True
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).exists():
            raise ValidationError("Пользователь с таким email уже существует")
        return email

class CustomUserChangeForm(UserChangeForm):
    """Форма для изменения пользователя в админке"""
    class Meta:
        model = User
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Убираем поле пароля из формы редактирования
        self.fields.pop('password', None)
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            # Проверяем, что email уникален, исключая текущего пользователя
            qs = User.objects.filter(email=email)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError("Пользователь с таким email уже существует")
        return email

class CustomUserCreationForm(UserCreationForm):
    """Форма для регистрации нового пользователя"""
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите email'
        })
    )
    first_name = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите имя'
        })
    )
    last_name = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите фамилию'
        })
    )
    phone_number = forms.CharField(
        required=False,
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+7 (999) 123-45-67'
        }),
        validators=[RegexValidator(
            regex=r'^\+?1?\d{9,15}$',
            message="Номер телефона должен быть в формате: '+79991234567'"
        )]
    )
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 
                  'phone_number', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите логин'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if field.widget.__class__ == forms.PasswordInput:
                field.widget.attrs.update({'class': 'form-control'})
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("Пользователь с таким email уже существует")
        return email

class CustomUserChangeForm(UserChangeForm):
    """Форма для изменения данных пользователя"""
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 
                  'phone_number', 'avatar')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
        
        # Убираем поле пароля из формы редактирования
        self.fields.pop('password')

class CustomAuthenticationForm(AuthenticationForm):
    """Кастомизированная форма входа"""
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Логин или email'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Пароль'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.error_messages['invalid_login'] = (
            "Неверный логин или пароль. "
            "Оба поля могут быть чувствительны к регистру."
        )

class PasswordChangeCustomForm(forms.Form):
    """Форма для смены пароля в профиле"""
    old_password = forms.CharField(
        label='Текущий пароль',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    new_password1 = forms.CharField(
        label='Новый пароль',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    new_password2 = forms.CharField(
        label='Подтвердите новый пароль',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    
    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
    
    def clean_old_password(self):
        old_password = self.cleaned_data.get('old_password')
        if not self.user.check_password(old_password):
            raise ValidationError("Неверный текущий пароль")
        return old_password
    
    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('new_password1')
        password2 = cleaned_data.get('new_password2')
        
        if password1 and password2 and password1 != password2:
            raise ValidationError("Пароли не совпадают")
        
        # Проверка сложности пароля
        if password1 and len(password1) < 8:
            raise ValidationError("Пароль должен содержать минимум 8 символов")
        
        return cleaned_data
class RegistrationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Введите ваш email'})
    )
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email, email_verified=True).exists():
            raise ValidationError('Этот email уже зарегистрирован и подтвержден.')
        return email

class VerificationForm(forms.Form):
    code = forms.CharField(
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите 6-значный код',
            'autocomplete': 'off'
        }),
        help_text="Введите код, отправленный на ваш email"
    )
    
    def clean_code(self):
        code = self.cleaned_data.get('code')
        if not code.isdigit() or len(code) != 6:
            raise ValidationError('Код должен состоять из 6 цифр')
        return code