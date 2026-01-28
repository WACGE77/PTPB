from django.urls import path

from terminal.consumers import SSHConsumer

urlpatterns = [

]


websocket_urlpatterns = [
    path('ssh/',SSHConsumer.as_asgi(),name='ssh')
]