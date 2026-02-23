# PTPB 堡垒机项目代码 Skill

## 创建新模块

### 1. 创建Django App
```bash
python manage.py startapp <app_name>
```

### 2. 添加到settings.py的INSTALLED_APPS
```python
INSTALLED_APPS = [
    ...
    '<app_name>',
]
```

### 3. 在BackEnd/urls.py添加路由
```python
path('api/<app_name>/', include('<app_name>.urls')),
```

---

## 创建新模型

### 1. 在app/models.py定义模型
```python
from django.db import models

class YourModel(models.Model):
    name = models.CharField(max_length=50)
    status = models.BooleanField(default=True)
    create_date = models.DateTimeField(auto_now_add=True)
    update_date = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'your_model'
```

### 2. 创建序列化器 (app/serialization.py)
```python
from rest_framework import serializers
from .models import YourModel

class YourModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = YourModel
        fields = '__all__'
```

### 3. 创建视图 (app/views.py)
使用Utils/modelViewSet.py的工厂函数:
```python
from Utils.modelViewSet import create_base_view_set
from .models import YourModel
from .serialization import YourModelSerializer
from Utils.Const import PERMISSIONS, AUDIT
from audit.Logging import OperaLogging

_YourModelViewSet = create_base_view_set(
    YourModel,
    YourModelSerializer,
    [BasePermission],  # 权限类
    PERMISSIONS.SYSTEM.XXX,  # 权限常量
    OperaLogging,
    AUDIT.CLASS.XXX,
    protect_key='protected',
)
class YourModelViewSet(_YourModelViewSet):
    pass
```

### 4. 添加URL路由 (app/urls.py)
```python
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import YourModelViewSet

router = DefaultRouter()
router.register('', YourModelViewSet, basename='yourmodel')

urlpatterns = [
    path('', include(router.urls)),
]
```

---

## 权限定义

### 1. 在Utils/Permissions.json添加权限
```json
{
  "SYSTEM": {
    "YOUR_OBJECT": {
      "CREATE": "system.yourobject.create",
      "DELETE": "system.yourobject.delete",
      "UPDATE": "system.yourobject.update",
      "READ": "system.yourobject.read"
    }
  }
}
```

### 2. 在Const.py中使用
```python
from Utils.Const import PERMISSIONS
# 权限码: PERMISSIONS.SYSTEM.YOUROBJECT.CREATE
```

---

## 添加审计日志

### 1. 在Utils/Audit.json添加审计类
```json
{
  "CLASS": {
    "YOUR_OBJECT": "your object"
  }
}
```

### 2. 在视图中使用
```python
from audit.Logging import OperaLogging

# 操作日志
OperaLogging.operation(request, '操作描述', True)

# 登录日志
OperaLogging.login(request, 'succeed'/'failed')

# 会话日志
OperaLogging.session(user, ip, resource, voucher, status, log)
```

---

## 自定义权限类

### 1. 继承BasePermission
```python
from perm.authentication import TokenPermission, get_code

class CustomPermission(TokenPermission):
    def auth(self, request, view):
        super().auth(request, view)
        permission_code = get_code(view)
        # 自定义权限检查逻辑
        return True
```

### 2. 在视图中使用
```python
class YourViewSet(CustomPermission):
    permission_code = PERMISSIONS.SYSTEM.XXX.READ
```

---

## WebSocket终端连接

### 1. 创建Consumer (terminal/consumers.py)
```python
from channels.generic.websocket import AsyncWebsocketConsumer

class YourConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
    
    async def disconnect(self, close_code):
        pass
    
    async def receive(self, text_data):
        # 处理消息
        await self.send(text_data='response')
```

### 2. 添加路由 (terminal/urls.py)
```python
from django.urls import path
from .consumers import YourConsumer

websocket_urlpatterns = [
    path('your_path/', YourConsumer.as_asgi()),
]
```

---

## 错误消息配置

### 在Utils/ErrorMsg.json添加
```json
{
  "ERROR": {
    "YOUR_ERROR": "your error message"
  }
}
```

### 在代码中使用
```python
from Utils.Const import ERRMSG
# ERRMSG.ERROR.YOUR_ERROR
```

---

## 响应格式

### 成功响应
```python
from Utils.Const import RESPONSE__200__SUCCESS, KEY
Response({**RESPONSE__200__SUCCESS, KEY.SUCCESS: data})
```

### 失败响应
```python
from Utils.Const import RESPONSE__400__FAILED, KEY
Response({**RESPONSE__400__FAILED, KEY.ERROR: error_msg})
```

---

## 分页查询

### 在ViewSet中使用
```python
class YourViewSet(RModelViewSet):
    @action(detail=False, methods=['get'], url_path='get')
    def get(self, request):
        # queryset会自动处理分页
        # 参数: page_number, page_size, all, desc
```
