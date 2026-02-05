from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from .forms import (CustomUserCreationForm, CustomAuthenticationForm, 
                   CustomUserChangeForm, PasswordChangeCustomForm)
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .forms import RegistrationForm, VerificationForm
from .models import EmailVerification, CustomUser
from .utils import generate_verification_code, send_verification_email

def register(request):
    """Регистрация нового пользователя"""
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            # Создаем пользователя, но не логиним его
            user = form.save(commit=False)
            user.is_active = True  # Пользователь активен, но email не подтвержден
            user.email_verified = False
            user.save()
            
            # Генерируем и отправляем код подтверждения
            code = generate_verification_code()
            EmailVerification.objects.create(user=user, code=code)
            
            # Отправляем email
            if send_verification_email(user, code):
                messages.success(request, f'Код подтверждения отправлен на email {user.email}')
            else:
                messages.warning(request, 'Ошибка отправки email. Попробуйте позже.')
            
            # Сохраняем ID пользователя в сессии для подтверждения
            request.session['verification_user_id'] = user.id
            return redirect('users:verify_email')
    else:
        form = RegistrationForm()
    
    return render(request, 'users/register.html', {'form': form})

def verify_email(request):
    """Подтверждение email с помощью кода"""
    user_id = request.session.get('verification_user_id')
    
    if not user_id:
        messages.error(request, 'Сессия истекла. Пожалуйста, пройдите регистрацию заново.')
        return redirect('users:register')
    
    user = get_object_or_404(CustomUser, id=user_id)
    
    if request.method == 'POST':
        form = VerificationForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['code']
            
            # Ищем актуальный код
            verification = EmailVerification.objects.filter(
                user=user,
                code=code,
                is_verified=False
            ).order_by('-created_at').first()
            
            if verification:
                if verification.is_expired():
                    messages.error(request, 'Код подтверждения истек. Запросите новый.')
                else:
                    # Подтверждаем email
                    verification.is_verified = True
                    verification.save()
                    
                    user.email_verified = True
                    user.save()
                    
                    # Автоматически логиним пользователя
                    login(request, user)
                    
                    # Очищаем сессию
                    if 'verification_user_id' in request.session:
                        del request.session['verification_user_id']
                    
                    messages.success(request, 'Email успешно подтвержден! Добро пожаловать!')
                    return redirect('core:home')
            else:
                messages.error(request, 'Неверный код подтверждения.')
    else:
        form = VerificationForm()
    
    # Проверяем, есть ли активные коды
    active_verifications = EmailVerification.objects.filter(
        user=user,
        is_verified=False,
        created_at__gte=timezone.now() - timezone.timedelta(minutes=15)
    ).exists()
    
    if not active_verifications:
        messages.warning(request, 'У вас нет активных кодов. Запросите новый код.')
    
    context = {
        'form': form,
        'user': user,
        'email': user.email[:3] + '***' + user.email[user.email.find('@'):]
    }
    
    return render(request, 'users/verify_email.html', context)

@require_POST
def resend_verification_code(request):
    """Повторная отправка кода подтверждения"""
    user_id = request.session.get('verification_user_id')
    
    if not user_id:
        return JsonResponse({'success': False, 'error': 'Сессия истекла'})
    
    user = get_object_or_404(CustomUser, id=user_id)
    
    # Проверяем, можно ли запросить новый код
    if not user.can_request_verification():
        return JsonResponse({
            'success': False, 
            'error': 'Вы можете запросить новый код только через 2 минуты после предыдущей отправки'
        })
    
    # Генерируем новый код
    code = generate_verification_code()
    EmailVerification.objects.create(user=user, code=code)
    
    # Отправляем email
    if send_verification_email(user, code):
        user.verification_code_sent_at = timezone.now()
        user.save()
        return JsonResponse({'success': True})
    else:
        return JsonResponse({'success': False, 'error': 'Ошибка отправки email'})

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