from django.urls import path

#from terminal.consumers import SSHConsumer
from terminal.views import Test


urlpatterns = [
    path('test/', Test.as_view(), name='test'),
]


websocket_urlpatterns = [
    #path('ssh/',SSHConsumer.as_asgi(),name='ssh')
]