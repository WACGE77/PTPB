import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BackEnd.settings')

django_asgi_app = get_asgi_application()

from terminal.consumers import SSHConsumer, RDPConsumer, MysqlConsumer

websocket_urlpatterns = [
    path('api/terminal/ssh/', SSHConsumer.as_asgi()),
    path('api/terminal/rdp/', RDPConsumer.as_asgi()),
    path('api/terminal/mysql/', MysqlConsumer.as_asgi()),
]

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": URLRouter(websocket_urlpatterns),
})
