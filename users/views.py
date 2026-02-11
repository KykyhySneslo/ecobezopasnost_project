from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from .forms import (CustomUserCreationForm, CustomAuthenticationForm, 
                   CustomUserChangeForm, PasswordChangeCustomForm)
from .models import CustomUser

def register_view(request):
    """Регистрация нового пользователя"""
    if request.user.is_authenticated:
        return redirect('core:home')
    
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Добро пожаловать, {user.first_name}! Регистрация прошла успешно.')
            return redirect('core:home')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'users/register.html', {'form': form})

def login_view(request):
    """Вход пользователя"""
    if request.user.is_authenticated:
        return redirect('core:home')
    
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Добро пожаловать, {user.first_name}!')
                
                # Перенаправляем на следующую страницу или на главную
                next_url = request.GET.get('next', 'core:home')
                return redirect(next_url)
    else:
        form = CustomAuthenticationForm()
    
    return render(request, 'users/login.html', {'form': form})

@login_required
def logout_view(request):
    """Выход пользователя"""
    logout(request)
    messages.info(request, 'Вы успешно вышли из системы.')
    return redirect('core:home')

@login_required
def profile_view(request):
    """Просмотр и редактирование профиля"""
    user = request.user
    
    if request.method == 'POST':
        # Обработка формы профиля
        if 'profile_form' in request.POST:
            profile_form = CustomUserChangeForm(request.POST, request.FILES, instance=user)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, 'Профиль успешно обновлен!')
                return redirect('users:profile')
        
        # Обработка формы смены пароля
        elif 'password_form' in request.POST:
            password_form = PasswordChangeCustomForm(user, request.POST)
            if password_form.is_valid():
                user.set_password(password_form.cleaned_data['new_password1'])
                user.save()
                update_session_auth_hash(request, user)  # Обновляем сессию
                messages.success(request, 'Пароль успешно изменен!')
                return redirect('users:profile')
    
    else:
        profile_form = CustomUserChangeForm(instance=user)
        password_form = PasswordChangeCustomForm(user)
    
    return render(request, 'users/profile.html', {
        'profile_form': profile_form,
        'password_form': password_form,
        'user': user,
    })

@login_required
def delete_avatar(request):
    """Удаление аватарки пользователя"""
    if request.method == 'POST':
        user = request.user
        if user.avatar:
            user.avatar.delete(save=False)
            user.avatar = None
            user.save()
            messages.success(request, 'Аватар успешно удален!')
    return redirect('users:profile')