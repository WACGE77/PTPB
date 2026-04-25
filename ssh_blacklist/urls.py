from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import DangerCommandRuleViewSet

router = DefaultRouter()
router.register(r'filter', DangerCommandRuleViewSet, basename='danger_cmd')

urlpatterns = []
urlpatterns += router.urls
