# PTPB 堡垒机后端项目

## 项目概述
基于 Django + Django REST Framework 的堡垒机后端系统，支持用户管理、角色权限控制、资源管理、WebSocket SSH连接和审计日志。

## 技术栈
- **框架**: Django 5.2 + DRF + Channels
- **认证**: JWT (simplejwt)
- **数据库**: SQLite3 (默认) / MySQL
- **WebSocket**: Channels + Daphne
- **SSH客户端**: asyncssh
- **其他**: django-filter, corsheaders

## 项目结构

```
PTPB/
├── BackEnd/              # Django项目配置
│   ├── settings.py       # 项目配置
│   ├── urls.py           # 主路由
│   ├── asgi.py           # ASGI配置
│   └── wsgi.py           # WSGI配置
├── rbac/                 # 用户角色权限模块
│   ├── models.py         # User, Role, Permission模型
│   ├── views.py          # 登录/登出/用户管理/角色管理
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
│   └── dynamic-routes.md # 动态路由文档
├── manage.py             # Django管理脚本
├── MEMORY.md             # 项目记忆体
└── requirements          # 依赖文件
```

## 核心模型

### rbac.models
- **User**: 用户 (account, password, name, email, roles, status, protected, phone_number, avatar, login_date)
- **Role**: 角色 (name, code, description, status, protected, perms)
- **Permission**: 权限 (scope, object, action, code, name)
- **UserRole**: 用户角色关联表
- **Route**: 路由 (path, component, title, icon, permission_code, parent_id, order, status)

### resource.models
- **Resource**: 主机资源 (name, status, ipv4_address/ipv6_address, domain, port, description, group, protocol, vouchers)
- **Voucher**: 登录凭证 (name, username, password/private_key, description, group)
- **ResourceGroup**: 资源分组 (name, description, protected, parent, level, root)
- **Protocol**: 协议 (name, code, description)

### perm.models
- **BaseAuth**: 角色-权限关联
- **ResourceGroupAuth**: 角色-资源组-权限关联 (带protected字段)

### audit.models
- **LoginLog**: 登录日志
- **OperationLog**: 操作日志
- **SessionLog**: SSH会话日志
- **ShellOperationLog**: Shell操作日志

## API路由

| 路径 | 模块 | 说明 |
|------|------|------|
| `/api/rbac/` | rbac | 用户/角色/权限管理 |
| `/api/rbac/routes/` | rbac | 动态路由API |
| `/api/perm/` | perm | 权限认证 |
| `/api/resource/` | resource | 资源管理 |
| `/api/terminal/` | terminal | WebSocket SSH连接 |
| `/api/audit/` | audit | 审计日志 |

## WebSocket路由

| 路径 | 模块 | 说明 |
|------|------|------|
| `/api/terminal/` | terminal | WebSocket SSH连接入口 |

## 认证机制

1. **Token认证**: 使用JWT (simplejwt)
   - AccessToken: 请求认证 (有效期200天)
   - RefreshToken: 刷新令牌 (有效期7天)

2. **权限控制**:
   - `TokenAuthorization`: JWT token认证
   - `TokenPermission`: 基于token的权限验证

## 权限体系

权限码格式: `{scope}.{object}.{action}`
- SYSTEM: 系统管理 (user, role, group, permission)
- RESOURCE: 资源管理 (self, voucher, group)
- AUDIT: 审计 (session, operation, login)
- USER: 用户个人 (profile)

## WebSocket SSH

- 路径: `/api/terminal/`
- 认证: 通过URL参数传递token
- 权限: 需要同时拥有资源读权限和凭证读权限
- 实现: 使用asyncssh库进行异步SSH连接

## 核心功能

1. **用户管理**: 支持用户的创建、编辑、删除和查询
2. **角色管理**: 支持角色的创建、编辑、删除和查询
3. **权限管理**: 基于角色的权限分配
4. **资源管理**: 管理主机资源和登录凭证
5. **资源分组**: 支持层级资源分组
6. **SSH终端**: 通过WebSocket实现的SSH终端
7. **审计日志**: 记录用户登录、操作和SSH会话日志
8. **动态路由**: 基于用户权限的动态前端路由生成

## 权限配置

### 页面权限
- **概述页面** (`/overview`): 需要 `user.profile.read` 权限（所有登录用户均可访问）
- **资源管理页面** (`/resource`): 需要 `user.profile.read` 权限（所有登录用户均可访问）
- **Web终端页面** (`/terminal`): 需要 `resource.self.read` 权限（需要资源访问权限）
- **权限管理页面** (`/permission_manage`): 无权限要求（所有登录用户均可访问）
- **用户管理页面** (`/user`): 需要 `system.user.read` 权限
- **角色管理页面** (`/role`): 需要 `system.role.read` 权限
- **审计日志页面** (`/audit`): 需要 `audit.session.read` 权限

### 资源数据权限
- 资源管理页面中的数据会根据用户的资源组权限进行筛选
- 用户只能看到自己有权访问的资源组中的资源
- Web终端需要同时拥有资源读权限和凭证读权限才能使用

## 开发命令

```bash
# 运行服务
python manage.py runserver
# 或使用daphne (支持WebSocket)
daphne -b 0.0.0.0 -p 8000 BackEnd.asgi:application

# 数据库迁移
python manage.py makemigrations
python manage.py migrate
```
