# PTPB 堡垒机后端项目

## 项目概述
基于 Django + Django REST Framework 的堡垒机后端系统，支持用户管理、角色权限控制、资源管理、WebSocket SSH连接和审计日志。

## 技术栈
- **框架**: Django 5.2 + DRF + Channels
- **认证**: JWT (simplejwt)
- **数据库**: SQLite3 (默认) / MySQL
- **WebSocket**: Channels + Daphne
- **其他**: django-filter, corsheaders, python-box

## 项目结构

```
PTPB/
├── BackEnd/              # Django项目配置
│   ├── settings.py       # 项目配置
│   ├── urls.py           # 主路由
│   └── asgi.py           # ASGI配置
├── rbac/                 # 用户角色权限模块
│   ├── models.py         # User, Role, Permission模型
│   ├── views.py          # 登录/登出/用户管理/角色管理
│   ├── serialization.py  # 序列化器
│   └── urls.py           # 路由
├── perm/                 # 认证授权模块
│   ├── authentication.py # Token认证和权限类
│   ├── models.py         # BaseAuth, ResourceGroupAuth
│   └── urls.py
├── resource/             # 资源管理模块
│   ├── models.py         # Resource, Voucher, ResourceGroup, Protocol
│   ├── views.py
│   ├── serialization.py
│   └── urls.py
├── terminal/             # 终端模块
│   ├── consumers.py      # WebSocket SSH连接
│   ├── protocol.py       # SSH协议实现
│   └── urls.py
├── audit/                # 审计日志模块
│   ├── models.py         # LoginLog, OperationLog, SessionLog, ShellOperationLog
│   ├── Logging.py        # 日志记录
│   └── views.py
├── Utils/                # 工具模块
│   ├── modelViewSet.py   # 通用ViewSet基类
│   ├── Const.py          # 常量配置
│   ├── before.py          # 工具函数
│   └── *.json            # 配置JSON文件
```

## 核心模型

### rbac.models
- **User**: 用户 (account, password, name, email, roles...)
- **Role**: 角色 (name, code, perms...)
- **Permission**: 权限 (scope, object, action, code, name)
- **UserRole**: 用户角色关联表

### resource.models
- **Resource**: 主机资源 (ip, port, protocol, group, vouchers)
- **Voucher**: 登录凭证 (username, password/private_key)
- **ResourceGroup**: 资源分组 (层级结构)
- **Protocol**: 协议 (SSH, RDP等)

### perm.models
- **BaseAuth**: 角色-权限关联
- **ResourceGroupAuth**: 角色-资源组-权限关联

### audit.models
- **LoginLog**: 登录日志
- **OperationLog**: 操作日志
- **SessionLog**: SSH会话日志
- **ShellOperationLog**: Shell操作日志

## API路由

| 路径 | 模块 | 说明 |
|------|------|------|
| `/api/rbac/` | rbac | 用户/角色/权限管理 |
| `/api/perm/` | perm | 权限认证 |
| `/api/resource/` | resource | 资源管理 |
| `/api/terminal/` | terminal | WebSocket SSH |
| `/api/audit/` | audit | 审计日志 |

## 认证机制

1. **Token认证**: 使用JWT (simplejwt)
   - AccessToken: 请求认证
   - RefreshToken: 刷新令牌

2. **权限控制**:
   - `BasePermission`: 基于角色权限
   - `ResourcePermission`: 资源级权限
   - `ResourceGroupPermission`: 资源组权限

## 权限体系

权限码格式: `{scope}.{object}.{action}`
- SYSTEM: 系统管理 (user, role, group, permission)
- RESOURCE: 资源管理 (self, voucher, group)
- AUDIT: 审计 (session, operation, login)
- USER: 用户个人 (profile)

## WebSocket SSH

- 路径: `/api/terminal/ssh/`
- 认证: 通过URL参数传递token
- 权限: 需要同时拥有资源读权限和凭证读权限

## 开发命令

```bash
# 运行服务
python manage.py runserver
# 或使用daphne (支持WebSocket)
daphne -b 0.0.0.0 -p 8000 BackEnd.asgi:application
```
