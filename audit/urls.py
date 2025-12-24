from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AuditALLViewSet,AuditSelfViewSet
audit_all_router = DefaultRouter()
audit_all_router.register('',AuditALLViewSet,basename='AuditALLViewSet')
audit_self_router = DefaultRouter()
audit_self_router.register('',AuditSelfViewSet,basename='AuditSelfViewSet')
urlpatterns = [
  path('all/',include(audit_all_router.urls)),
  path('self/',include(audit_self_router.urls))
]