# PTPB 堡垒机后端项目架构文档

## 1. 项目概述

PTPB 是一个基于 Django + Django REST Framework 的堡垒机后端系统，支持用户管理、角色权限控制、资源管理、WebSocket SSH连接和审计日志等核心功能。

### 1.1 核心功能

- **用户管理**: 支持用户的创建、编辑、删除和查询
- **角色管理**: 支持角色的创建、编辑、删除和查询
- **权限管理**: 基于角色的权限分配
- **资源管理**: 管理主机资源和登录凭证
- **资源分组**: 支持层级资源分组
- **SSH终端**: 通过WebSocket实现的SSH终端
- **审计日志**: 记录用户登录、操作和SSH会话日志
- **动态路由**: 基于用户权限的动态前端路由生成

## 2. 技术栈

- **框架**: Django 5.2 + DRF + Channels
- **认证**: JWT (simplejwt)
- **数据库**: SQLite3 (默认) / MySQL
- **WebSocket**: Channels + Daphne
- **SSH客户端**: asyncssh
- **其他**: django-filter, corsheaders

## 3. 项目结构

```
PTPB/
├── BackEnd/              # Django项目配置
│   ├── settings.py       # 项目配置
│   ├── urls.py           # 主路由
│   ├── asgi.py           # ASGI配置
│   └── wsgi.py           # WSGI配置
├── rbac/                 # 用户角色权限模块
│   ├── models.py         # User, Role, Permission, Route模型
│   ├── views.py          # 登录/登出/用户管理/角色管理/动态路由
│   ├── serialization.py  # 序列化器
│   └── urls.py           # 路由
├── perm/                 # 认证授权模块
│   ├── authentication.py # Token认证和权限类
│   ├── models.py         # BaseAuth, ResourceGroupAuth
│   └── urls.py           # 路由
├── resource/             # 资源管理模块
│   ├── models.py         # Resource, Voucher, ResourceGroup, Protocol
│   ├── views.py          # 资源管理视图
│   ├── serialization.py  # 序列化器
│   └── urls.py           # 路由
├── terminal/             # 终端模块
│   ├── consumers.py      # WebSocket SSH连接处理
│   ├── protocol.py       # SSH协议实现 (AsyncSSHClient)
│   ├── serialization.py  # 序列化器
│   └── urls.py           # 路由
├── audit/                # 审计日志模块
│   ├── models.py         # 日志模型
│   ├── Logging.py        # 日志记录工具
│   ├── views.py          # 审计日志视图
│   └── urls.py           # 路由
├── Utils/                # 工具模块
│   ├── modelViewSet.py   # 通用ViewSet基类
│   ├── Const.py          # 常量配置
│   ├── before.py         # 工具函数
│   ├── after.py          # 工具函数
│   └── *.json            # 配置JSON文件 (Audit, Config, ErrorMsg, Key, Method, Permissions, Response)
├── docs/                 # 文档目录
│   ├── API_DOC.md        # API文档
│   ├── CODE_SKILL.md     # 代码技能文档
│   ├── dynamic-routes.md # 动态路由文档
│   └── ARCHITECTURE.md   # 架构文档
├── manage.py             # Django管理脚本
├── MEMORY.md             # 项目记忆体
└── requirements          # 依赖文件
```

## 4. 核心模块详解

### 4.1 认证授权模块 (perm)

#### 4.1.1 核心功能
- **Token认证**: 使用JWT进行身份验证
- **权限控制**: 基于角色的权限验证
- **资源组权限**: 细粒度的资源访问控制

#### 4.1.2 关键类
- `TokenAuthorization`: JWT token认证
- `TokenPermission`: 基于token的权限验证
- `BasePermission`: 系统权限验证
- `ResourcePermission`: 资源权限验证
- `ResourceGroupPermission`: 资源组权限验证
- `AuditPermission`: 审计权限验证

### 4.2 用户角色权限模块 (rbac)

#### 4.2.1 核心功能
- **用户管理**: 创建、编辑、删除、查询用户
- **角色管理**: 创建、编辑、删除、查询角色
- **权限管理**: 分配角色权限
- **动态路由**: 基于用户权限生成前端路由

#### 4.2.2 关键模型
- `User`: 用户模型
- `Role`: 角色模型
- `Permission`: 权限模型
- `Route`: 路由模型
- `UserRole`: 用户角色关联表

### 4.3 资源管理模块 (resource)

#### 4.3.1 核心功能
- **资源管理**: 管理主机资源
- **凭证管理**: 管理登录凭证
- **资源分组**: 支持层级资源分组

#### 4.3.2 关键模型
- `Resource`: 主机资源模型
- `Voucher`: 登录凭证模型
- `ResourceGroup`: 资源分组模型
- `Protocol`: 协议模型

### 4.4 终端模块 (terminal)

#### 4.4.1 核心功能
- **WebSocket SSH连接**: 实现浏览器中的SSH终端
- **会话管理**: 管理SSH会话
- **终端操作记录**: 记录终端操作

#### 4.4.2 关键类
- `SSHConsumer`: WebSocket SSH连接处理
- `AsyncSSHClient`: SSH协议实现

### 4.5 审计日志模块 (audit)

#### 4.5.1 核心功能
- **登录日志**: 记录用户登录情况
- **操作日志**: 记录用户操作
- **会话日志**: 记录SSH会话
- **Shell操作日志**: 记录Shell操作

#### 4.5.2 关键模型
- `LoginLog`: 登录日志模型
- `OperationLog`: 操作日志模型
- `SessionLog`: SSH会话日志模型
- `ShellOperationLog`: Shell操作日志模型

### 4.6 工具模块 (Utils)

#### 4.6.1 核心功能
- **通用ViewSet**: 提供CRUD操作的通用实现
- **常量配置**: 定义系统常量
- **工具函数**: 提供通用工具函数
- **配置文件**: 存储系统配置

#### 4.6.2 关键文件
- `modelViewSet.py`: 通用ViewSet基类
- `Const.py`: 常量配置
- `before.py`: 工具函数
- `after.py`: 工具函数
- `Permissions.json`: 权限配置
- `Response.json`: 响应格式配置
- `ErrorMsg.json`: 错误消息配置

## 5. 权限体系

### 5.1 权限码格式

权限码格式: `{scope}.{object}.{action}`

- **SYSTEM**: 系统管理 (user, role, group, permission)
- **RESOURCE**: 资源管理 (self, voucher, group)
- **AUDIT**: 审计 (session, operation, login)
- **USER**: 用户个人 (profile)

### 5.2 页面权限

| 页面 | 路径 | 权限码 | 说明 |
|------|------|--------|------|
| 概述页面 | `/overview` | `user.profile.read` | 所有登录用户均可访问 |
| 资源管理页面 | `/resource` | `user.profile.read` | 所有登录用户均可访问 |
| Web终端页面 | `/terminal` | `resource.self.read` | 需要资源访问权限 |
| 权限管理页面 | `permission_manage` | 无 | 所有登录用户均可访问 |
| 用户管理页面 | `/user` | `system.user.read` | 需要系统用户读权限 |
| 角色管理页面 | `/role` | `system.role.read` | 需要系统角色读权限 |
| 审计日志页面 | `/audit` | `audit.session.read` | 需要审计会话读权限 |

### 5.3 资源数据权限

- 资源管理页面中的数据会根据用户的资源组权限进行筛选
- 用户只能看到自己有权访问的资源组中的资源
- Web终端需要同时拥有资源读权限和凭证读权限才能使用

## 6. API 架构

### 6.1 核心API

| 路径 | 模块 | 说明 |
|------|------|------|
| `/api/rbac/` | rbac | 用户/角色/权限管理 |
| `/api/rbac/routes/` | rbac | 动态路由API |
| `/api/perm/` | perm | 权限认证 |
| `/api/resource/` | resource | 资源管理 |
| `/api/terminal/` | terminal | WebSocket SSH连接 |
| `/api/audit/` | audit | 审计日志 |

### 6.2 WebSocket路由

| 路径 | 模块 | 说明 |
|------|------|------|
| `/api/terminal/` | terminal | WebSocket SSH连接入口 |

## 7. 认证机制

### 7.1 Token认证

- **AccessToken**: 请求认证 (有效期200天)
- **RefreshToken**: 刷新令牌 (有效期7天)

### 7.2 认证流程

1. 用户登录获取token
2. 前端在请求头中携带token
3. 后端验证token并提取用户信息
4. 根据用户角色和权限进行授权

## 8. 动态路由实现

### 8.1 核心逻辑

1. 从数据库查询所有启用的路由
2. 构建路由树结构
3. 获取用户拥有的权限
4. 根据用户权限过滤路由
5. 返回过滤后的路由树

### 8.2 关键代码

```python
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
        from perm.models import BaseAuth, ResourceGroupAuth
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

## 9. 开发指南

### 9.1 添加新功能的流程

1. **分析需求**: 确定新功能的需求和范围
2. **设计架构**: 设计新功能的架构和实现方案
3. **创建模型**: 如果需要，创建新的数据库模型
4. **实现视图**: 实现API视图和业务逻辑
5. **添加路由**: 在urls.py中添加新的路由
6. **编写序列化器**: 创建对应的序列化器
7. **添加权限**: 配置权限控制
8. **编写测试**: 编写测试用例
9. **更新文档**: 更新API文档和架构文档

### 9.2 代码规范

- **代码风格**: 遵循PEP 8规范
- **命名规范**: 使用蛇形命名法 (snake_case)
- **模型设计**: 合理使用ForeignKey, ManyToManyField
- **权限控制**: 严格遵循最小权限原则
- **审计日志**: 记录所有关键操作
- **错误处理**: 统一错误响应格式
- **性能优化**: 合理使用数据库索引，避免N+1查询
- **安全措施**: 密码加密存储，避免明文传输

### 9.3 部署建议

1. **生产环境**: 使用MySQL数据库
2. **WebSocket**: 使用Daphne服务器
3. **静态文件**: 使用Nginx或CDN
4. **安全**: 配置HTTPS，设置合理的CORS策略
5. **监控**: 配置日志监控，定期备份数据库

## 10. 总结

PTPB 堡垒机后端项目采用了模块化的架构设计，将不同功能分离到独立的模块中，提高了代码的可维护性和可扩展性。项目使用Django和DRF作为基础框架，结合Channels实现了WebSocket SSH连接，提供了完整的堡垒机功能。

通过本架构文档，开发者可以了解项目的整体结构、核心功能和实现方式，为后续的功能扩展和维护提供参考。