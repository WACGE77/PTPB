from django.urls import path

from terminal.consumers import SSHConsumer, RDPConsumer, MysqlConsumer

urlpatterns = [
]


websocket_urlpatterns = [
    path('ssh/', SSHConsumer.as_asgi(), name='ssh'),
    path('rdp/', RDPConsumer.as_asgi(), name='rdp'),
    path('mysql/', MysqlConsumer.as_asgi(), name='mysql')
]