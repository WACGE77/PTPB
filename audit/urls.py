from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LoginLogViewSet,OperationLogViewSet,SessionLogViewSet,ShellOperationLogViewSet
login_router = DefaultRouter()
login_router.register('',LoginLogViewSet,basename='LoginLogViewSet')
opera_router = DefaultRouter()
opera_router.register('',OperationLogViewSet,basename='OperationLogViewSet')
session_router = DefaultRouter()
session_router.register('',SessionLogViewSet,basename='SessionLogViewSet')
shell_op_router = DefaultRouter()
shell_op_router.register('',ShellOperationLogViewSet,basename='ShellOperationLogViewSet')
urlpatterns = [
  path('login/',include(login_router.urls)),
  path('opera/',include(opera_router.urls)),
  path('session/',include(session_router.urls)),
  path('shell_op/',include(shell_op_router.urls))
]
