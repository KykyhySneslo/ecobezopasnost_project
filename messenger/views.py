from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.contrib.auth import get_user_model
from .models import Conversation, Message, EmployeeStatus

User = get_user_model()

@login_required
def inbox(request):
    """Входящие для обычных пользователей"""
    if request.user.is_employee:
        return redirect('messenger:employee_inbox')
    
    # Получаем диалог пользователя с сотрудником
    conversation = Conversation.objects.filter(user=request.user).first()
    
    if conversation:
        return redirect('messenger:chat', conversation_id=conversation.id)
    
    # Если нет диалога, проверяем доступных сотрудников
    available_employees = User.objects.filter(
        is_employee=True,
        is_active=True
    )
    
    if available_employees.exists():
        # Перенаправляем к первому доступному сотруднику
        return redirect('messenger:start_conversation', user_id=available_employees.first().id)
    
    # Если сотрудников нет, показываем страницу без сотрудников
    return render(request, 'messenger/no_employees.html')

@login_required
def employee_inbox(request):
    """Входящие для сотрудников"""
    if not request.user.is_employee:
        return redirect('messenger:inbox')
    
    # Получаем все диалоги сотрудника
    conversations = Conversation.objects.filter(
        employee=request.user
    ).select_related('user').prefetch_related('messages').order_by('-updated_at')
    
    # Добавляем количество непрочитанных сообщений
    for conversation in conversations:
        conversation.unread_count = conversation.messages.filter(
            is_read=False
        ).exclude(sender=request.user).count()
    
    # Получаем пользователей без диалогов
    users_without_conversations = User.objects.filter(
        is_employee=False,
        is_active=True
    ).exclude(
        user_conversations__employee=request.user
    )
    
    context = {
        'conversations': conversations,
        'available_users': users_without_conversations,
    }
    
    return render(request, 'messenger/employee_inbox.html', context)

@login_required
def chat(request, conversation_id):
    """Страница чата"""
    conversation = get_object_or_404(Conversation, id=conversation_id)
    
    # Проверка прав доступа
    if request.user != conversation.user and request.user != conversation.employee:
        return redirect('messenger:inbox')
    
    # Обновляем время последнего посещения чата
    if request.user == conversation.user:
        conversation.user_last_seen = timezone.now()
    else:
        conversation.employee_last_seen = timezone.now()
    conversation.save()
    
    # Получаем статус собеседника
    if request.user.is_employee:
        # Если текущий пользователь - сотрудник, то собеседник - пользователь
        # Проверяем, является ли собеседник сотрудником
        if conversation.user.is_employee:
            employee_status = EmployeeStatus.objects.filter(employee=conversation.user).first()
        else:
            # Обычный пользователь - у него нет EmployeeStatus
            employee_status = None
    else:
        # Если текущий пользователь - не сотрудник, то собеседник - сотрудник
        employee_status = EmployeeStatus.objects.filter(employee=conversation.employee).first()
    
    # Получаем последние сообщения
    messages = Message.objects.filter(conversation=conversation).order_by('timestamp')[:50]
    
    context = {
        'conversation': conversation,
        'messages': messages,
        'employee_status': employee_status,
    }
    
    return render(request, 'messenger/chat.html', context)

@login_required
@require_POST
def send_message(request, conversation_id):
    """Отправка сообщения через AJAX"""
    conversation = get_object_or_404(Conversation, id=conversation_id)
    
    # Проверка прав доступа
    if request.user != conversation.user and request.user != conversation.employee:
        return JsonResponse({'success': False, 'errors': ['Нет доступа']})
    
    text = request.POST.get('text', '').strip()
    file = request.FILES.get('file')
    
    if not text and not file:
        return JsonResponse({'success': False, 'errors': ['Сообщение не может быть пустым']})
    
    # Создаем сообщение
    message = Message.objects.create(
        conversation=conversation,
        sender=request.user,
        text=text,
    )
    
    # Обработка файла
    if file:
        message.file = file
        message.file_name = file.name
        message.file_type = file.content_type
        message.save()
    
    # Обновляем время диалога
    conversation.updated_at = timezone.now()
    conversation.save()
    
    # Подготавливаем данные для ответа
    message_data = {
        'id': message.id,
        'text': message.text,
        'sender_id': message.sender.id,
        'sender_name': message.sender.get_full_name() or message.sender.username,
        'sender_is_employee': message.sender.is_employee,
        'timestamp': message.timestamp.isoformat(),
        'is_read': message.is_read,
        'file': {
            'url': message.file.url if message.file else None,
            'name': message.file_name,
            'type': message.file_type,
            'size': message.get_file_size_display(),
            'icon': message.get_file_icon(),
        } if message.file else None,
    }
    
    return JsonResponse({'success': True, 'message': message_data})

@login_required
@require_POST
def delete_conversation(request, conversation_id):
    """Удаление диалога"""
    conversation = get_object_or_404(Conversation, id=conversation_id)
    
    # Проверка прав доступа (только сотрудник может удалить)
    if request.user != conversation.employee:
        return JsonResponse({'success': False, 'error': 'Нет прав на удаление'})
    
    # Удаляем диалог
    conversation.delete()
    
    return JsonResponse({'success': True})

@login_required
def start_conversation(request, user_id):
    """Начало нового диалога"""
    employee = get_object_or_404(User, id=user_id, is_employee=True, is_active=True)
    
    # Проверяем, есть ли уже диалог
    conversation = Conversation.objects.filter(
        user=request.user,
        employee=employee
    ).first()
    
    if conversation:
        return redirect('messenger:chat', conversation_id=conversation.id)
    
    # Создаем новый диалог
    conversation = Conversation.objects.create(
        user=request.user,
        employee=employee
    )
    
    return redirect('messenger:chat', conversation_id=conversation.id)

@login_required
def unread_count(request):
    """Получение количества непрочитанных сообщений"""
    if request.user.is_employee:
        # Для сотрудника - непрочитанные сообщения от пользователей
        unread_count = Message.objects.filter(
            conversation__employee=request.user,
            is_read=False
        ).exclude(sender=request.user).count()
    else:
        # Для пользователя - непрочитанные сообщения от сотрудников
        unread_count = Message.objects.filter(
            conversation__user=request.user,
            is_read=False
        ).exclude(sender=request.user).count()
    
    return JsonResponse({'unread_count': unread_count})

@login_required
@require_POST
def update_status(request):
    """Обновляет статус онлайн пользователя"""
    if request.user.is_employee:
        status, created = EmployeeStatus.objects.get_or_create(
            employee=request.user
        )
        status.last_seen = timezone.now()
        status.save()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})