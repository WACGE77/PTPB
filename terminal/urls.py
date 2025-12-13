from django.urls import path

from terminal.views import Test

urlpatterns = [
    path('test/', Test.as_view(), name='test'),
]
