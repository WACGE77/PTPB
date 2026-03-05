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
    [TokenPermission],  # 权限类
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

### 1. 继承TokenPermission
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

### 1. 创建SSH Consumer (terminal/consumers.py)
```python
from channels.generic.websocket import AsyncWebsocketConsumer
from terminal.protocol import AsyncSSHClient
from audit.Logging import OperaLogging

class SSHConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # 解析参数
        params = parse_qs(self.scope['query_string'].decode('utf-8'))
        # 获取客户端IP
        self.ip = get_ws_client_ip(self.scope)
        # 接受连接
        await self.accept()
        # 认证
        auth, msg = await self.auth(params)
        if not auth:
            await self.disable(msg)
            return
        # 建立SSH连接
        conned, msg = await self.pty_connect(self.send, self.close)
        if not conned:
            await self.disable(msg)
            return
        # 启动处理任务
        self.handle_task = asyncio.create_task(self.handle())

    async def disconnect(self, close_code):
        # 关闭SSH连接
        if self.pty and self.pty.get_status:
            await self.pty.close()
        # 取消处理任务
        if self.handle_task:
            self.handle_task.cancel()

    async def receive(self, text_data=None, bytes_data=None):
        # 处理客户端消息
        try:
            data = json.loads(text_data)
            await self.data_queue.put(data)
        except JSONDecodeError:
            pass
```

### 2. 使用AsyncSSHClient
```python
from terminal.protocol import AsyncSSHClient

# 创建客户端实例
client = AsyncSSHClient()

# 设置回调
client.set_recv_callback(self.send)
client.set_on_disconnect(self.close)

# 连接SSH
await client.connect(host, username, password, port)

# 发送命令
await client.send('ls -l\n')

# 调整终端大小
await client.resize(cols, rows)

# 关闭连接
await client.close()
```

### 3. 添加WebSocket路由 (terminal/urls.py)
```python
from django.urls import path
from .consumers import SSHConsumer

websocket_urlpatterns = [
    path('ssh/', SSHConsumer.as_asgi()),
]
```

### 4. 在BackEnd/urls.py添加WebSocket路由
```python
from terminal.urls import websocket_urlpatterns as terminal
from channels.routing import URLRouter

websocket_urlpatterns = [
    path('api/terminal/', URLRouter(terminal))
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

---

## 资源分组管理

### 1. 创建资源分组
```python
from resource.models import ResourceGroup

# 创建根分组
group = ResourceGroup.objects.create(
    name='Root Group',
    description='Root resource group'
)

# 创建子分组
child_group = ResourceGroup.objects.create(
    name='Child Group',
    description='Child resource group',
    parent=group
)
```

### 2. 资源分组权限
```python
from perm.models import ResourceGroupAuth
from rbac.models import Role, Permission

# 创建资源组权限
ResourceGroupAuth.objects.create(
    role=role,
    permission=permission,
    resource_group=resource_group
)
```

---

## SSH凭证管理

### 1. 创建SSH凭证
```python
from resource.models import Voucher

# 密码凭证
voucher = Voucher.objects.create(
    name='Test Voucher',
    username='root',
    password='password123',
    group=resource_group
)

# 密钥凭证
voucher = Voucher.objects.create(
    name='Test Key Voucher',
    username='root',
    private_key='-----BEGIN RSA PRIVATE KEY-----...',
    group=resource_group
)
```

### 2. 关联资源和凭证
```python
resource.vouchers.add(voucher)
```

---

## 异步编程

### 1. 使用async/await
```python
async def your_async_function():
    # 异步操作
    result = await some_async_operation()
    return result
```

### 2. 创建异步任务
```python
import asyncio

# 创建任务
task = asyncio.create_task(your_async_function())

# 等待任务完成
result = await task

# 取消任务
task.cancel()
```

---

## 开发最佳实践

1. **代码风格**: 遵循PEP 8规范
2. **命名规范**: 使用蛇形命名法 (snake_case)
3. **模型设计**: 合理使用ForeignKey, ManyToManyField
4. **权限控制**: 严格遵循最小权限原则
5. **审计日志**: 记录所有关键操作
6. **错误处理**: 统一错误响应格式
7. **性能优化**: 合理使用数据库索引，避免N+1查询
8. **安全措施**: 密码加密存储，避免明文传输

---

## 动态路由实现

### 1. 路由模型创建

```python
# rbac/models.py
from django.db import models

class Route(models.Model):
    class Meta:
        db_table = 'route'
    id = models.AutoField(primary_key=True)
    path = models.CharField(max_length=255, unique=True)
    component = models.CharField(max_length=255)
    title = models.CharField(max_length=100)
    icon = models.CharField(max_length=100)
    permission_code = models.CharField(max_length=100, null=True, blank=True)
    parent_id = models.IntegerField(null=True, blank=True)
    order = models.IntegerField(default=0)
    status = models.BooleanField(default=True)
    create_date = models.DateTimeField(auto_now_add=True)
    update_date = models.DateTimeField(auto_now=True)
```

### 2. 动态路由API实现

```python
# rbac/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Route
from perm.authentication import TokenAuthorization, TokenPermission
from Utils.Const import RESPONSE__200__SUCCESS, KEY
from perm.models import BaseAuth, ResourceGroupAuth

class DynamicRoutesView(APIView):
    authentication_classes = [TokenAuthorization]
    permission_classes = [TokenPermission]
    
    def get(self, request):
        # 从数据库查询所有启用的路由
        routes = Route.objects.filter(status=True).order_by('order')
        
        # 构建路由树
        route_dict = {}
        root_routes = []
        
        # 首先创建所有路由的route_data并添加到route_dict中
        for route in routes:
            route_data = {
                "path": route.path,
                "component": route.component,
                "meta": {
                    "title": route.title,
                    "icon": route.icon,
                    "permission": route.permission_code
                },
                "children": []
            }
            route_dict[route.id] = route_data
        
        # 然后构建路由树
        for route in routes:
            if route.parent_id is None:
                root_routes.append(route_dict[route.id])
            else:
                if route.parent_id in route_dict:
                    route_dict[route.parent_id]["children"].append(route_dict[route.id])
        
        # 获取用户拥有的权限
        user_permissions = set()
        for role in request.user.roles.all():
            # 通过BaseAuth表获取权限
            auths = BaseAuth.objects.filter(role=role)
            for auth in auths:
                user_permissions.add(auth.permission.code)
            # 通过ResourceGroupAuth表获取权限
            resource_auths = ResourceGroupAuth.objects.filter(role=role)
            for auth in resource_auths:
                user_permissions.add(auth.permission.code)
        
        # 过滤路由
        def filter_routes(routes_list):
            filtered = []
            for route in routes_list:
                if "children" in route and route["children"]:
                    filtered_children = filter_routes(route["children"])
                    if filtered_children:
                        route["children"] = filtered_children
                        filtered.append(route)
                else:
                    permission = route.get("meta", {}).get("permission")
                    if permission:
                        # 直接检查用户是否有对应的权限码
                        if permission in user_permissions:
                            filtered.append(route)
                    else:
                        # 没有权限要求的路由直接添加
                        filtered.append(route)
            return filtered
        
        # 过滤路由
        filtered_routes = filter_routes(root_routes)
        
        return Response({**RESPONSE__200__SUCCESS, KEY.SUCCESS: filtered_routes}, status=status.HTTP_200_OK)
```

### 3. 添加动态路由URL

```python
# rbac/urls.py
from django.urls import path
from .views import DynamicRoutesView

urlpatterns = [
    # 其他路由...
    path('routes/', DynamicRoutesView.as_view(), name='dynamic-routes'),
]
```

### 4. 测试动态路由

#### 创建测试脚本

```python
# test_scripts/test_routes.py
import requests
import json

# 测试动态路由API
def test_dynamic_routes():
    # 登录获取token
    login_url = 'http://localhost:8000/api/rbac/login/'
    login_data = {
        'account': 'administrator',
        'password': 'administrator'
    }
    
    response = requests.post(login_url, json=login_data)
    if response.status_code == 200:
        token = response.json()['token']['access']
        
        # 请求动态路由
        routes_url = 'http://localhost:8000/api/rbac/routes/'
        headers = {
            'Authorization': f'Bearer {token}'
        }
        
        routes_response = requests.get(routes_url, headers=headers)
        if routes_response.status_code == 200:
            print("动态路由API测试成功")
            print("返回的路由:")
            print(json.dumps(routes_response.json(), indent=2, ensure_ascii=False))
        else:
            print(f"动态路由API测试失败: {routes_response.status_code}")
            print(routes_response.json())
    else:
        print(f"登录失败: {response.status_code}")
        print(response.json())

if __name__ == '__main__':
    test_dynamic_routes()
```

#### 多用户测试脚本

```python
# test_scripts/test_multi_user_routes.py
import requests
import json

# 测试不同用户的路由权限
def test_user_routes(username, password, user_type):
    print(f"\n测试用户: {username} ({user_type})")
    
    # 登录获取token
    login_url = 'http://localhost:8000/api/rbac/login/'
    login_data = {
        'account': username,
        'password': password
    }
    
    response = requests.post(login_url, json=login_data)
    if response.status_code == 200:
        token = response.json()['token']['access']
        
        # 请求动态路由
        routes_url = 'http://localhost:8000/api/rbac/routes/'
        headers = {
            'Authorization': f'Bearer {token}'
        }
        
        routes_response = requests.get(routes_url, headers=headers)
        if routes_response.status_code == 200:
            routes = routes_response.json()['detail']
            print(f"获取到 {len(routes)} 个路由")
            for route in routes:
                print(f"- {route['meta']['title']} ({route['path']}) - 权限: {route['meta'].get('permission')}")
        else:
            print(f"获取路由失败: {routes_response.status_code}")
            print(routes_response.json())
    else:
        print(f"登录失败: {response.status_code}")
        print(response.json())

if __name__ == '__main__':
    # 测试管理员用户
    test_user_routes('administrator', 'administrator', '管理员')
    
    # 测试普通用户
    test_user_routes('testuser', 'testuser', '普通用户')
```

### 5. 权限配置

#### 页面权限设置

| 页面 | 路径 | 权限码 | 说明 |
|------|------|--------|------|
| 概述页面 | `/overview` | `user.profile.read` | 所有登录用户均可访问 |
| 资源管理页面 | `/resource` | `user.profile.read` | 所有登录用户均可访问 |
| Web终端页面 | `/terminal` | `resource.self.read` | 需要资源访问权限 |
| 权限管理页面 | `permission_manage` | 无 | 所有登录用户均可访问 |
| 用户管理页面 | `/user` | `system.user.read` | 需要系统用户读权限 |
| 角色管理页面 | `/role` | `system.role.read` | 需要系统角色读权限 |
| 审计日志页面 | `/audit` | `audit.session.read` | 需要审计会话读权限 |

#### 资源数据权限

- 资源管理页面中的数据会根据用户的资源组权限进行筛选
- 用户只能看到自己有权访问的资源组中的资源
- Web终端需要同时拥有资源读权限和凭证读权限才能使用

## 部署建议

1. **生产环境**: 使用MySQL数据库
2. **WebSocket**: 使用Daphne服务器
3. **静态文件**: 使用Nginx或CDN
4. **安全**: 配置HTTPS，设置合理的CORS策略
5. **监控**: 配置日志监控，定期备份数据库
