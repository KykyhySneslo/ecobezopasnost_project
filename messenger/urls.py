from django.urls import path
from . import views

app_name = 'messenger'

urlpatterns = [
    path('', views.inbox, name='inbox'),
    path('employee/', views.employee_inbox, name='employee_inbox'),
    path('chat/<int:conversation_id>/', views.chat, name='chat'),
    path('send/<int:conversation_id>/', views.send_message, name='send_message'),
    path('delete/<int:conversation_id>/', views.delete_conversation, name='delete_conversation'),
    path('start/<int:user_id>/', views.start_conversation, name='start_conversation'),
    path('unread_count/', views.unread_count, name='unread_count'),
    path('update_status/', views.update_status, name='update_status'),
]