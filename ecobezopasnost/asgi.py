import os
import django
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack 

# Устанавливаем настройки Django ДО импорта приложений
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecobezopasnost.settings')
django.setup()

# Теперь импортируем routing ПОСЛЕ django.setup()
from messenger import routing

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(  
        URLRouter(
            routing.websocket_urlpatterns
        )
    ),
})