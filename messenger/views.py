from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Q, Count, Max
from django.utils import timezone
from .models import Conversation, Message, EmployeeStatus
from .forms import MessageForm

User = get_user_model()

@login_required
def inbox(request):
    """Список диалогов пользователя"""
    try:
        if request.user.is_employee:
            # Для сотрудника: все диалоги, где он сотрудник
            conversations = Conversation.objects.filter(
                employee=request.user,
                is_active=True
            ).select_related('user').prefetch_related('messages').annotate(
                unread_count=Count('messages', filter=Q(messages__is_read=False) & ~Q(messages__sender=request.user)),
                last_message_time=Max('messages__timestamp')
            ).order_by('-last_message_time', '-updated_at')
            
            # Получаем список всех пользователей, у которых нет диалога с этим сотрудником
            existing_users = conversations.values_list('user_id', flat=True)
            available_users = User.objects.filter(
                is_employee=False,
                is_active=True
            ).exclude(
                id__in=existing_users
            ).exclude(
                id=request.user.id
            )
            
            return render(request, 'messenger/employee_inbox.html', {
                'conversations': conversations,
                'available_users': available_users,
            })
        else:
            # Для обычного пользователя: его диалог с сотрудником
            conversation = Conversation.objects.filter(
                user=request.user,
                is_active=True
            ).first()
            
            # Если диалога нет, создаем с первым доступным сотрудником
            if not conversation:
                employee = User.objects.filter(
                    is_employee=True,
                    is_active=True
                ).first()
                
                if not employee:
                    # Перенаправляем на страницу "нет сотрудников"
                    return render(request, 'messenger/no_employees.html')
                
                conversation = Conversation.objects.create(
                    user=request.user,
                    employee=employee,
                    is_active=True
                )
            
            return redirect('messenger:chat', conversation_id=conversation.id)
            
    except Exception as e:
        print(f"Error in inbox view: {e}")
        return render(request, 'messenger/error.html', {
            'error_message': 'Произошла ошибка при загрузке мессенджера.'
        })

@login_required
def chat(request, conversation_id):
    """Чат в конкретном диалоге (WebSocket версия)"""
    try:
        conversation = get_object_or_404(
            Conversation.objects.select_related('user', 'employee'),
            id=conversation_id,
            is_active=True
        )
        
        # Проверка прав доступа
        if request.user not in [conversation.user, conversation.employee]:
            return render(request, 'messenger/error.html', {
                'error_message': 'У вас нет доступа к этому диалогу.'
            })
        
        # Получаем историю сообщений
        messages_list = conversation.messages.select_related('sender').order_by('timestamp')
        
        # Помечаем сообщения как прочитанные
        if not request.user.is_employee:
            # Для пользователя: помечаем сообщения сотрудника как прочитанные
            conversation.messages.filter(
                sender=conversation.employee,
                is_read=False
            ).update(is_read=True)
        else:
            # Для сотрудника: помечаем сообщения пользователя как прочитанные
            conversation.messages.filter(
                sender=conversation.user,
                is_read=False
            ).update(is_read=True)
        
        # Получаем статус сотрудника
        employee_status = EmployeeStatus.objects.filter(employee=conversation.employee).first()
        
        return render(request, 'messenger/chat.html', {
            'conversation': conversation,
            'messages': messages_list,
            'employee_status': employee_status,
            'form': MessageForm(),
        })
        
    except Exception as e:
        print(f"Error in chat view: {e}")
        return render(request, 'messenger/error.html', {
            'error_message': 'Произошла ошибка при загрузке чата.'
        })

@login_required
@require_http_methods(["POST"])
def send_message(request, conversation_id):
    """Отправка сообщения (для HTTP запросов, например, файлов)"""
    try:
        conversation = get_object_or_404(Conversation, id=conversation_id, is_active=True)
        
        # Проверка прав доступа
        if request.user not in [conversation.user, conversation.employee]:
            return JsonResponse({'error': 'Access denied'}, status=403)
        
        form = MessageForm(request.POST, request.FILES)
        
        if form.is_valid():
            message = form.save(commit=False)
            message.conversation = conversation
            message.sender = request.user
            
            # Обработка файла
            if 'file' in request.FILES:
                message.file = request.FILES['file']
            
            message.save()
            
            # Формируем полные данные сообщения для ответа
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
                    'icon': message.get_file_icon(),
                    'size_display': message.get_file_size_display(),
                } if message.file else None,
            }
            
            # Обновляем время диалога
            conversation.save()
            
            return JsonResponse({
                'success': True,
                'message': message_data,
            })
        
        return JsonResponse({'errors': form.errors}, status=400)
        
    except Exception as e:
        print(f"Error in send_message: {e}")
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def start_conversation(request, user_id):
    """Начать новый диалог (для сотрудника)"""
    if not request.user.is_employee:
        return redirect('messenger:inbox')
    
    user = get_object_or_404(User, id=user_id, is_employee=False)
    
    # Проверяем, есть ли уже диалог
    conversation, created = Conversation.objects.get_or_create(
        user=user,
        employee=request.user,
        defaults={'is_active': True}
    )
    
    return redirect('messenger:chat', conversation_id=conversation.id)

@login_required
def get_unread_count(request):
    """Получить количество непрочитанных сообщений"""
    if request.user.is_employee:
        unread_count = Message.objects.filter(
            conversation__employee=request.user,
            is_read=False
        ).exclude(sender=request.user).count()
    else:
        unread_count = Message.objects.filter(
            conversation__user=request.user,
            is_read=False
        ).exclude(sender=request.user).count()
    
    return JsonResponse({'unread_count': unread_count})

@login_required
def mark_all_as_read(request, conversation_id):
    """Пометить все сообщения как прочитанные"""
    conversation = get_object_or_404(Conversation, id=conversation_id)
    
    # Проверка прав доступа
    if request.user not in [conversation.user, conversation.employee]:
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    # Помечаем сообщения от собеседника как прочитанные
    if request.user.is_employee:
        conversation.messages.filter(
            sender=conversation.user,
            is_read=False
        ).update(is_read=True)
    else:
        conversation.messages.filter(
            sender=conversation.employee,
            is_read=False
        ).update(is_read=True)
    
    return JsonResponse({'success': True})

@login_required
def delete_conversation(request, conversation_id):
    """Удалить диалог (для сотрудника)"""
    if not request.user.is_employee:
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    conversation = get_object_or_404(Conversation, id=conversation_id, employee=request.user)
    conversation.delete()
    
    return JsonResponse({'success': True})