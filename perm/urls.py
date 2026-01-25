from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AuthorizationViewSet
base_router = DefaultRouter()
base_router.register('', AuthorizationViewSet, basename='resource-group-auth')
# role_bind = DefaultRouter()
# role_bind.register('',RoleBindManageViewSet,basename='role-bind')

urlpatterns = [
    path('group-auth/', include(base_router.urls),name='base-auth'),
    #path('role-bind/', include(role_bind.urls),name='role-bind'),
]
