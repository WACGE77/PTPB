
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import LoginView, LogoutView, RefreshView, UserManagerViewSet, PermissionListView, RoleManagerViewSet, DynamicRoutesView

user_manager_router = DefaultRouter()
user_manager_router.register('', UserManagerViewSet, basename='usermanager')
role_manager_router = DefaultRouter()
role_manager_router.register('', RoleManagerViewSet, basename='role')

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('refresh/', RefreshView.as_view(), name='refresh'),
    path('user/', include(user_manager_router.urls), name='usermanager'),
    path('role/', include(role_manager_router.urls), name='rolemanager'),
    path('perm/',PermissionListView.as_view(), name='permissionlist'),
    path('routes/', DynamicRoutesView.as_view(), name='dynamic-routes'),

]