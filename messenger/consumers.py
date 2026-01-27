import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import Conversation, Message, EmployeeStatus

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """Обработка подключения к WebSocket"""
        self.user = self.scope["user"]
        
        if not self.user.is_authenticated:
            await self.close()
            return
        
        # Получаем ID диалога из URL
        self.conversation_id = self.scope['url_route']['kwargs'].get('conversation_id')
        
        if not self.conversation_id:
            await self.close()
            return
        
        # Проверяем, есть ли у пользователя доступ к этому диалогу
        conversation = await self.get_conversation(self.conversation_id)
        if not conversation:
            await self.close()
            return
        
        # Создаем имя группы для этого диалога
        self.room_group_name = f'chat_{self.conversation_id}'
        
        # Присоединяемся к группе
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        # Обновляем статус сотрудника (если он онлайн)
        if self.user.is_employee:
            await self.update_employee_status(self.user.id, True)
        
        await self.accept()
        
        # Отправляем историю сообщений
        await self.send_history()

    async def disconnect(self, close_code):
        """Обработка отключения от WebSocket"""
        # Убираем из группы
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        
        # Обновляем статус сотрудника (если он уходит)
        if self.user.is_employee:
            await self.update_employee_status(self.user.id, False)

    async def receive(self, text_data):
        """Получение сообщения от клиента"""
        data = json.loads(text_data)
        message_type = data.get('type')
        
        if message_type == 'message':
            text = data.get('text', '').strip()
            file_data = data.get('file')
            
            if text or file_data:
                # Сохраняем сообщение в БД
                message = await self.save_message(text, file_data)
                
                # Отправляем сообщение всем в группе
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'chat_message',
                        'message': await self.message_to_json(message),
                        'sender_id': self.user.id,
                    }
                )
        
        elif message_type == 'typing':
            # Отправляем статус "печатает"
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_typing',
                    'user_id': self.user.id,
                    'username': self.user.get_full_name() or self.user.username,
                    'is_typing': data.get('is_typing', False),
                }
            )
        
        elif message_type == 'read':
            # Отмечаем сообщения как прочитанные
            await self.mark_as_read(data.get('message_ids', []))

    async def chat_message(self, event):
        """Отправка сообщения клиенту"""
        await self.send(text_data=json.dumps({
            'type': 'message',
            'message': event['message'],
            'sender_id': event['sender_id'],
        }))

    async def user_typing(self, event):
        """Отправка статуса "печатает" клиенту"""
        await self.send(text_data=json.dumps({
            'type': 'typing',
            'user_id': event['user_id'],
            'username': event['username'],
            'is_typing': event['is_typing'],
        }))

    @database_sync_to_async
    def get_conversation(self, conversation_id):
        """Получение диалога из БД"""
        try:
            conversation = Conversation.objects.get(id=conversation_id)
            # Проверяем права доступа
            if self.user == conversation.user or self.user == conversation.employee:
                return conversation
        except Conversation.DoesNotExist:
            return None
        return None

    @database_sync_to_async
    def save_message(self, text, file_data=None):
        """Сохранение сообщения в БД"""
        conversation = Conversation.objects.get(id=self.conversation_id)
        
        message = Message.objects.create(
            conversation=conversation,
            sender=self.user,
            text=text,
        )
        
        # Обработка файла (в реальном проекте нужна обработка base64/бинарных данных)
        if file_data:
            # Здесь будет логика сохранения файла
            pass
        
        # Обновляем время последнего обновления диалога
        conversation.save()
        
        return message

    @database_sync_to_async
    def update_employee_status(self, employee_id, is_online):
        """Обновление статуса сотрудника"""
        try:
            status, created = EmployeeStatus.objects.get_or_create(
                employee_id=employee_id
            )
            status.is_online = is_online
            status.save()
        except Exception as e:
            print(f"Error updating employee status: {e}")

    @database_sync_to_async
    def mark_as_read(self, message_ids):
        """Пометить сообщения как прочитанные"""
        Message.objects.filter(
            id__in=message_ids,
            conversation_id=self.conversation_id
        ).exclude(sender=self.user).update(is_read=True)

    @database_sync_to_async
    def get_message_history(self, limit=50):
        """Получение истории сообщений"""
        messages = Message.objects.filter(
            conversation_id=self.conversation_id
        ).select_related('sender').order_by('timestamp')[:limit]
        
        return [self.message_to_json_sync(message) for message in messages]

    def message_to_json_sync(self, message):
        """Синхронная версия преобразования сообщения в JSON"""
        return {
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

    async def message_to_json(self, message):
        """Асинхронная версия преобразования сообщения в JSON"""
        return await database_sync_to_async(self.message_to_json_sync)(message)

    async def send_history(self):
        """Отправка истории сообщений клиенту"""
        history = await self.get_message_history()
        await self.send(text_data=json.dumps({
            'type': 'history',
            'messages': history,
        }))