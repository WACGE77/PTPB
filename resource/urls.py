
from django.urls import path, include
from rest_framework.routers import DefaultRouter

#from .views import  ResourceViewSet,ResourceVoucherViewSet,ResourceBindVoucherView

resource_manager_router = DefaultRouter()
#resource_manager_router.register('', ResourceViewSet, basename='usermanager')
voucher_manager_router = DefaultRouter()
#voucher_manager_router.register('',ResourceVoucherViewSet,basename='vouchermanager')
urlpatterns = [
    path('resource/', include(resource_manager_router.urls), name='resource'),
    path('voucher/',include(voucher_manager_router.urls),name='voucher'),
    #path('resourcebindvoucher/',ResourceBindVoucherView.as_view(),name='resourcebindvoucher ')
]