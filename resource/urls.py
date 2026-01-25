
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import  ResourceViewSet,VoucherViewSet,ResourceGroupViewSet

resource_manager_router = DefaultRouter()
resource_manager_router.register('', ResourceViewSet, basename='usermanager')
voucher_manager_router = DefaultRouter()
voucher_manager_router.register('',VoucherViewSet,basename='vouchermanager')
resource_group_manager_router = DefaultRouter()
resource_group_manager_router.register('', ResourceGroupViewSet, basename='resource_group')

urlpatterns = [
    path('resource/', include(resource_manager_router.urls), name='resource'),
    path('voucher/',include(voucher_manager_router.urls),name='voucher'),
    path('group/',include(resource_group_manager_router.urls),name='group'),
]