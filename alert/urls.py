from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import GlobalSMTPConfigViewSet, AlertMethodViewSet, AlertTemplateViewSet, ProbeRuleViewSet, ProbeLogViewSet, TestEmailView

# 创建路由器
router = DefaultRouter()

# 注册视图集
router.register(r'smtp', GlobalSMTPConfigViewSet, basename='global_smtp_config')
router.register(r'method', AlertMethodViewSet, basename='alert_method')
router.register(r'template', AlertTemplateViewSet, basename='alert_template')
router.register(r'rule', ProbeRuleViewSet, basename='probe_rule')
router.register(r'log', ProbeLogViewSet, basename='probe_log')

# 额外的URL模式
urlpatterns = [
    # 测试邮件发送API
    path('smtp/test-email/', TestEmailView.as_view(), name='test_email'),
]

# 添加路由器生成的URL模式
urlpatterns += router.urls
