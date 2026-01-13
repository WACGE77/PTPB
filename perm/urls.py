from django.urls import path, include
from rest_framework.routers import DefaultRouter
#from .views import BaseAuthManageViewSet
#base_router = DefaultRouter()
#base_router.register('', BaseAuthManageViewSet, basename='base-auth')
# role_bind = DefaultRouter()
# role_bind.register('',RoleBindManageViewSet,basename='role-bind')

urlpatterns = [
    #path('base-auth/', include(base_router.urls),name='base-auth'),
    # path('role-bind/', include(role_bind.urls),name='role-bind'),
]
