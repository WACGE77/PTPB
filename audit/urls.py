from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LoginLogViewSet,OperationLogViewSet,SessionLogViewSet
login_router = DefaultRouter()
login_router.register('',LoginLogViewSet,basename='LoginLogViewSet')
opera_router = DefaultRouter()
opera_router.register('',OperationLogViewSet,basename='OperationLogViewSet')
session_router = DefaultRouter()
session_router.register('',SessionLogViewSet,basename='SessionLogViewSet')
urlpatterns = [
  path('login/',include(login_router.urls)),
  path('opera/',include(opera_router.urls)),
  path('session/',include(session_router.urls))
]
