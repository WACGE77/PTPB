
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import  LoginView, LogoutView, RefreshView, UserManagerViewSet

usermanager_router = DefaultRouter()
usermanager_router.register('', UserManagerViewSet, basename='usermanager')

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('refresh/', RefreshView.as_view(), name='refresh'),
    path('user/', include(usermanager_router.urls), name='usermanager'),
]