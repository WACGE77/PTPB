from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import SSHCommandFilterViewSet

# 创建路由器
router = DefaultRouter()

# 注册SSH命令过滤规则视图集
router.register(r'filter', SSHCommandFilterViewSet, basename='ssh_filter')

# 额外的URL模式
urlpatterns = [
]

# 添加路由器生成的URL模式
urlpatterns += router.urls
