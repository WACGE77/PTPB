# PTPB 堡垒机后端接口文档

## 基础信息

- **基础URL**: `https://设备/api/`
- **WebSocket**: `ws://设备/api/terminal/`
- **认证方式**: JWT Token (Bearer Token)
- **Content-Type**: `application/json`

## 通用响应格式

### 成功响应
```json
{
    "code": 200,
    "msg": "OK",
    "detail": {},
    "total": 10
}
```

### 失败响应
```json
{
    "code": 400,
    "msg": "参数错误",
    "detail": "错误信息"
}
```

### 分页参数
| 参数 | 类型 | 说明 |
|------|------|------|
| page_number | int | 页码 (默认1) |
| page_size | int | 每页数量 (默认10, 最大100) |
| all | bool | 获取全部数据 |
| desc | bool | 降序排列 |

---

## 一、认证接口 (rbac)

### 1. 用户登录
**POST** `/rbac/login/`

**请求体**:
```json
{
    "account": "administrator",
    "password": "administrator"
}
```

**响应**:
```json
{
    "code": 200,
    "msg": "OK",
    "token": {
        "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    }
}
```

**异常响应**:
```json
{
    "code": 401,
    "msg": "未登录",
    "detail": "密码错误"
}
```

---

### 2. 用户登出
**POST** `/rbac/logout/`

**请求头**: `Authorization: Bearer <access_token>`

**响应**:
```json
{
    "code": 200,
    "msg": "OK"
}
```

**异常响应**:
```json
{
    "detail": "未登录"
}
```

---

### 3. 刷新Token
**POST** `/rbac/refresh/`

**Cookie**: `refresh=<refresh_token>`

**响应**:
```json
{
    "code": 200,
    "msg": "OK",
    "token": {
        "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    }
}
```

**异常响应**:
```json
{
    "code": 400,
    "msg": "参数错误"
}
```

---

## 二、用户管理 (rbac)

### 4. 添加用户
**POST** `/rbac/user/add/`

**请求头**: `Authorization: Bearer <access_token>`

**请求体**:
```json
{
    "account": "test11",
    "password": "admin123",
    "name": "测试",
    "email": "2811986118@qq.com",
    "status": true,
    "phone_number": null,
    "remark": null
}
```

**响应**:
```json
{
    "code": 200,
    "msg": "OK"
}
```

**异常响应**:
```json
{
    "code": 400,
    "msg": "参数错误",
    "detail": {
        "account": ["账户以被注册"]
    }
}
```

---

### 5. 修改用户
**POST** `/rbac/user/edit/`

**请求头**: `Authorization: Bearer <access_token>`

**请求体**:
```json
{
    "id": 12,
    "email": "example@test.com",
    "name": "test111",
    "phone_number": "17531333029",
    "remark": "备注"
}
```

**响应**:
```json
{
    "code": 200,
    "msg": "OK"
}
```

**异常响应**:
```json
{
    "code": 400,
    "msg": "参数错误",
    "detail": {
        "email": ["邮箱已被注册"],
        "phone_number": ["具有 电话 的 用户 已存在。"]
    }
}
```

---

### 6. 删除用户
**POST** `/rbac/user/del/`

**请求头**: `Authorization: Bearer <access_token>`

**请求体**:
```json
{
    "id_list": [1, 2]
}
```

**响应**:
```json
{
    "code": 200,
    "msg": "OK"
}
```

**异常响应**:
```json
{
    "code": 400,
    "msg": "参数错误",
    "detail": "用户受保护,或对象不存在"
}
```

---

### 7. 查看用户
**GET** `/rbac/user/get/`

**请求头**: `Authorization: Bearer <access_token>`

**查询参数**:
```json
{
    "page_size": 2,
    "name": "tes"
}
```

**响应**:
```json
{
    "code": 200,
    "msg": "OK",
    "total": 2,
    "detail": [
        {
            "id": 1,
            "account": "administrator",
            "name": "管理员",
            "email": "1964282264@qq.com",
            "status": true,
            "protected": true,
            "phone_number": null,
            "avatar": "/media/avatars/default.png",
            "create_date": "2025-01-01T08:00:00+08:00",
            "update_date": "2025-01-01T08:00:00+08:00",
            "login_date": null,
            "remark": null,
            "roles": [1]
        }
    ],
    "extra": null
}
```

---

### 8. 重置自身密码
**POST** `/rbac/user/reset_password/`

**请求头**: `Authorization: Bearer <access_token>`

**请求体**:
```json
{
    "old_password": "administrator",
    "new_password": "admin123"
}
```

**响应**:
```json
{
    "code": 200,
    "msg": "OK"
}
```

**异常响应**:
```json
{
    "code": 400,
    "msg": "参数错误",
    "detail": {
        "new_password": ["新旧密码不能相同"]
    }
}
```

---

### 9. 查询自身信息
**GET** `/rbac/user/detail/`

**请求头**: `Authorization: Bearer <access_token>`

**响应**:
```json
{
    "code": 200,
    "msg": "OK",
    "detail": {
        "id": 1,
        "account": "administrator",
        "name": "管理员",
        "email": "1964282264@qq.com",
        "status": true,
        "protected": true,
        "phone_number": null,
        "avatar": "/media/avatars/default.png",
        "create_date": "2025-01-01T08:00:00+08:00",
        "update_date": "2025-01-01T08:00:00+08:00",
        "login_date": null,
        "remark": null,
        "roles": [1],
        "ip": "127.0.0.1"
    }
}
```

---

### 10. 绑定用户角色
**POST** `/rbac/user/role/`

**请求头**: `Authorization: Bearer <access_token>`

**请求体**:
```json
{
    "id": 1,
    "roles": [1]
}
```

**响应**:
```json
{
    "code": 200,
    "msg": "OK"
}
```

**异常响应**:
```json
{
    "code": 400,
    "msg": "参数错误",
    "detail": "无法操作系统保留项"
}
```

---

## 三、角色管理 (rbac)

### 11. 添加角色
**POST** `/rbac/role/add/`

**请求头**: `Authorization: Bearer <access_token>`

**请求体**:
```json
{
    "name": "test",
    "code": "test",
    "description": "测试"
}
```

**响应**:
```json
{
    "code": 200,
    "msg": "OK"
}
```

**异常响应**:
```json
{
    "code": 400,
    "msg": "参数错误",
    "detail": {
        "name": ["具有 name 的 role 已存在。"],
        "code": ["具有 code 的 role 已存在。"]
    }
}
```

---

### 12. 修改角色
**POST** `/rbac/role/edit/`

**请求头**: `Authorization: Bearer <access_token>`

**请求体**:
```json
{
    "id": 2,
    "name": "test21",
    "code": "test111",
    "description": "测试"
}
```

**响应**:
```json
{
    "code": 200,
    "msg": "OK"
}
```

**异常响应**:
```json
{
    "code": 400,
    "msg": "参数错误",
    "detail": "无法操作系统保留项"
}
```

---

### 13. 删除角色
**POST** `/rbac/role/del/`

**请求头**: `Authorization: Bearer <access_token>`

**请求体**:
```json
{
    "id_list": [1, 2]
}
```

**响应**:
```json
{
    "code": 200,
    "msg": "OK",
    "total": 1
}
```

**异常响应**:
```json
{
    "code": 400,
    "msg": "参数错误",
    "detail": "角色受保护,或对象不存在"
}
```

---

### 14. 查看角色
**GET** `/rbac/role/get/`

**请求头**: `Authorization: Bearer <access_token>`

**查询参数**:
```json
{
    "page_size": 1,
    "all": true,
    "name": "管"
}
```

**响应**:
```json
{
    "code": 200,
    "msg": "OK",
    "total": 1,
    "detail": [
        {
            "id": 1,
            "name": "管理员",
            "code": "Administrator",
            "description": "超级管理员",
            "status": true,
            "protected": true,
            "create_date": "2025-01-01T08:00:00+08:00",
            "update_date": "2025-01-01T08:00:00+08:00"
        }
    ],
    "extra": null
}
```

---

### 15. 查看角色系统权限
**GET** `/rbac/role/get/permission/`

**请求头**: `Authorization: Bearer <access_token>`

**查询参数**:
```json
{
    "id": 1
}
```

**响应**:
```json
{
    "code": 200,
    "msg": "OK",
    "detail": {
        "id": 3,
        "perms": [16, 17, 18]
    }
}
```

**异常响应**:
```json
{
    "detail": "未找到。"
}
```

---

### 16. 授权角色系统权限
**POST** `/rbac/role/edit/permission/`

**请求头**: `Authorization: Bearer <access_token>`

**请求体**:
```json
{
    "id": 5,
    "perms": [1, 2, 3, 4, 5, 6, 7, 8, 9]
}
```

**响应**:
```json
{
    "code": 200,
    "msg": "OK"
}
```

**异常响应**:
```json
{
    "code": 400,
    "msg": "参数错误",
    "detail": {
        "perms": ["权限错误"]
    }
}
```

---

### 17. 获取权限列表
**GET** `/rbac/perm/`

**请求头**: `Authorization: Bearer <access_token>`

**响应**:
```json
{
    "code": 200,
    "msg": "OK",
    "detail": [
        {
            "id": 1,
            "scope": "system",
            "object": "user",
            "action": "create",
            "code": "system.user.create",
            "name": "创建用户"
        }
    ]
}
```

---

## 四、资源组权限管理 (perm)

### 18. 查看角色资源组权限
**GET** `/perm/group-auth/get/`

**请求头**: `Authorization: Bearer <access_token>`

**查询参数**:
```json
{
    "role_id": 1
}
```

**响应**:
```json
{
    "code": 200,
    "msg": "OK",
    "detail": [
        {
            "id": 1,
            "protected": true,
            "create_date": "2025-01-01T08:00:00+08:00",
            "role": 1,
            "permission": 21,
            "resource_group": 1
        }
    ]
}
```

**异常响应**:
```json
{
    "detail": "未找到。"
}
```

---

### 19. 授权角色资源组权限
**POST** `/perm/group-auth/edit/`

**请求头**: `Authorization: Bearer <access_token>`

**请求体**:
```json
{
    "role_id": 1,
    "groups": [
        {
            "id": 2,
            "permission": [16, 17, 18, 19, 20, 21, 22, 23]
        }
    ]
}
```

**说明**: permission数组内的值为权限ID，

**响应**:
范围16-23```json
{
    "code": 200,
    "msg": "OK"
}
```

**异常响应**:
```json
{
    "code": 400,
    "msg": "参数错误",
    "detail": {
        "groups": {
            "0": {
                "id": {
                    "group": "所添加至的组不存在"
                }
            }
        }
    }
}
```

---

## 五、资源组管理 (resource)

### 20. 添加资源组
**POST** `/resource/group/add/`

**请求头**: `Authorization: Bearer <access_token>`

**请求体**:
```json
{
    "name": "测试组",
    "description": "测试描述",
    "parent": null,
    "role": 1
}
```

**说明**: 
- 顶级组不需要 parent，但需要 role
- 子组需要 parent，且需要拥有父级组的资源管理权限

**响应**:
```json
{
    "code": 200,
    "msg": "OK"
}
```

**异常响应**:
```json
{
    "code": 400,
    "msg": "参数错误",
    "detail": {
        "name": ["名称已被占用"]
    }
}
```

---

### 21. 修改资源组
**POST** `/resource/group/edit/`

**请求头**: `Authorization: Bearer <access_token>`

**请求体**:
```json
{
    "id": 3,
    "description": "改了啊,不是摸鱼了"
}
```

**响应**:
```json
{
    "code": 200,
    "msg": "OK"
}
```

**异常响应**:
```json
{
    "code": 400,
    "msg": "参数错误",
    "detail": "无法操作系统保留项"
}
```

---

### 22. 删除资源组
**POST** `/resource/group/del/`

**请求头**: `Authorization: Bearer <access_token>`

**请求体**:
```json
{
    "id_list": [1, 2]
}
```

**响应**:
```json
{
    "code": 200,
    "msg": "OK"
}
```

**异常响应**:
```json
{
    "code": 400,
    "msg": "参数错误",
    "detail": "无法操作系统保留项"
}
```

---

### 23. 查看资源组
**GET** `/resource/group/get/`

**请求头**: `Authorization: Bearer <access_token>`

**响应**:
```json
{
    "code": 200,
    "msg": "OK",
    "total": 2,
    "detail": [
        {
            "id": 1,
            "name": "Default",
            "description": "默认资源部组",
            "create_date": "2025-01-01T08:00:00+08:00",
            "update_date": "2025-01-01T08:00:00+08:00",
            "level": 0,
            "parent": null,
            "root": 1
        }
    ],
    "extra": null
}
```

**异常响应**:
```json
{
    "code": 403,
    "msg": "权限错误"
}
```

---

## 六、资源管理 (resource)

### 24. 添加资源
**POST** `/resource/resource/add/`

**请求头**: `Authorization: Bearer <access_token>`

**请求体**:
```json
{
    "name": "ptp",
    "ipv4_address": "106.13.85.137",
    "group": 1,
    "protocol": 1
}
```

**响应**:
```json
{
    "code": 200,
    "msg": "OK"
}
```

**异常响应**:
```json
{
    "code": 400,
    "msg": "参数错误",
    "detail": {
        "voucher": ["不同系统组,禁止使用"]
    }
}
```

---

### 25. 修改资源
**POST** `/resource/resource/edit/`

**请求头**: `Authorization: Bearer <access_token>`

**请求体**:
```json
{
    "id": 3,
    "description": "改了啊,不是摸鱼了"
}
```

**响应**:
```json
{
    "code": 200,
    "msg": "OK"
}
```

**异常响应**:
```json
{
    "detail": "有关联当前组数据,无法切组"
}
```

---

### 26. 删除资源
**POST** `/resource/resource/del/`

**请求头**: `Authorization: Bearer <access_token>`

**请求体**:
```json
{
    "id_list": [1, 2]
}
```

**响应**:
```json
{
    "code": 200,
    "msg": "OK"
}
```

**异常响应**:
```json
{
    "detail": "错误参数"
}
```

---

### 27. 查看资源
**GET** `/resource/resource/get/`

**请求头**: `Authorization: Bearer <access_token>`

**响应**:
```json
{
    "code": 200,
    "msg": "OK",
    "total": 1,
    "detail": [
        {
            "id": 1,
            "vouchers": [
                {
                    "id": 1,
                    "name": "ptp",
                    "username": "root",
                    "description": null,
                    "create_date": "2026-02-05T13:55:41.559349+08:00",
                    "update_date": "2026-02-05T13:55:41.559367+08:00",
                    "group": 1
                }
            ],
            "name": "ptp",
            "status": true,
            "ipv4_address": "106.13.85.137",
            "ipv6_address": null,
            "domain": null,
            "port": 22,
            "description": null,
            "create_date": "2026-02-05T13:55:38.477859+08:00",
            "update_date": "2026-02-05T14:03:48.490958+08:00",
            "group": 1,
            "protocol": 1
        }
    ],
    "extra": [
        {
            "id": 1,
            "name": "Default",
            "description": "默认资源部组",
            "create_date": "2025-01-01T08:00:00+08:00",
            "update_date": "2025-01-01T08:00:00+08:00",
            "level": 0,
            "parent": null,
            "root": 1
        }
    ]
}
```

**异常响应**:
```json
{
    "code": 403,
    "msg": "权限错误"
}
```

---

## 七、凭证管理 (resource)

### 28. 添加凭证
**POST** `/resource/voucher/add/`

**请求头**: `Authorization: Bearer <access_token>`

**请求体**:
```json
{
    "name": "ptp",
    "username": "root",
    "password": "wen9369494260.0",
    "group": 2
}
```

**注意**: `password` 和 `private_key` 必须二选一

**响应**:
```json
{
    "code": 200,
    "msg": "OK"
}
```

**异常响应**:
```json
{
    "code": 400,
    "msg": "参数错误",
    "detail": {
        "name": ["名称已被占用"]
    }
}
```

---

### 29. 修改凭证
**POST** `/resource/voucher/edit/`

**请求头**: `Authorization: Bearer <access_token>`

**请求体**:
```json
{
    "id": 1,
    "name": "ptp",
    "username": "root",
    "password": "wen9369494260.0",
    "private_key": null,
    "description": null,
    "group": 2
}
```

**响应**:
```json
{
    "code": 200,
    "msg": "OK"
}
```

**异常响应**:
```json
{
    "detail": "有关联当前组数据,无法切组"
}
```

---

### 30. 删除凭证
**POST** `/resource/voucher/del/`

**请求头**: `Authorization: Bearer <access_token>`

**请求体**:
```json
{
    "id_list": [1, 2]
}
```

**响应**:
```json
{
    "code": 200,
    "msg": "OK"
}
```

**异常响应**:
```json
{
    "detail": "错误参数"
}
```

---

### 31. 查看凭证
**GET** `/resource/voucher/get/`

**请求头**: `Authorization: Bearer <access_token>`

**响应**:
```json
{
    "code": 200,
    "msg": "OK",
    "total": 1,
    "detail": [
        {
            "id": 1,
            "name": "ptp",
            "username": "root",
            "description": null,
            "create_date": "2026-02-12T15:21:02.158396+08:00",
            "update_date": "2026-02-13T12:34:12.671695+08:00",
            "group": 1
        }
    ],
    "extra": null
}
```

**异常响应**:
```json
{
    "code": 403,
    "msg": "权限错误"
}
```

---

## 八、审计日志 (audit)

### 32. 查看登录日志
**GET** `/audit/login/get/`

**请求头**: `Authorization: Bearer <access_token>`

**查询参数**:
```json
{
    "self": true,
    "desc": true
}
```

**响应**:
```json
{
    "code": 200,
    "msg": "OK",
    "total": 29,
    "detail": [
        {
            "id": 29,
            "user": {
                "id": 1,
                "name": "管理员"
            },
            "ip": "127.0.0.1",
            "status": "succeed",
            "date": "2026-02-11T13:53:46.004920+08:00"
        }
    ],
    "extra": null
}
```

**异常响应**:
```json
{
    "code": 403,
    "msg": "权限错误"
}
```

---

### 33. 查看操作日志
**GET** `/audit/opera/get/`

**请求头**: `Authorization: Bearer <access_token>`

**查询参数**:
```json
{
    "self": true,
    "operation": "添加"
}
```

**响应**:
```json
{
    "code": 200,
    "msg": "OK",
    "total": 17,
    "detail": [
        {
            "id": 1,
            "user": {
                "id": 1,
                "name": "管理员"
            },
            "ip": "127.0.0.1",
            "operation": "添加资源",
            "status": true,
            "date": "2026-02-05T13:55:38.502920+08:00"
        }
    ],
    "extra": null
}
```

**异常响应**:
```json
{
    "code": 403,
    "msg": "权限错误"
}
```

---

### 34. 查看会话日志
**GET** `/audit/session/get/`

**请求头**: `Authorization: Bearer <access_token>`

**查询参数**:
```json
{
    "self": true,
    "resource": "p"
}
```

**响应**:
```json
{
    "code": 200,
    "msg": "OK",
    "total": 3,
    "detail": [
        {
            "id": 1,
            "user": {
                "id": 1,
                "name": "管理员"
            },
            "resource": {
                "id": 1,
                "name": "ptp",
                "ip": "106.13.85.137"
            },
            "voucher": {
                "id": 1,
                "username": "root"
            },
            "start_time": "2026-02-05T20:34:30.443360+08:00",
            "end_time": "2026-02-05T20:34:34.869207+08:00",
            "status": "close",
            "ip": "127.0.0.1"
        }
    ],
    "extra": null
}
```

**异常响应**:
```json
{
    "code": 403,
    "msg": "权限错误"
}
```

---

## 九、WebSocket SSH连接 (terminal)

### 35. SSH连接
**WebSocket** `/terminal/ssh/`

**连接参数** (Query String):
```
ws://设备/api/terminal/ssh/?token=<access_token>&resource_id=1&voucher_id=1
```

**消息格式** (客户端 → 服务器):
```json
{
    "type": 1,
    "data": {
        "cols": 80,
        "rows": 24
    }
}
```
- Type 1: 调整终端大小

```json
{
    "type": 2,
    "data": "ls -la\n"
}
```
- Type 2: 发送命令

**消息格式** (服务器 → 客户端):
- 直接发送终端输出文本

**关闭连接**: 发送空消息或关闭WebSocket

---

## 错误码说明

| code | msg | 说明 |
|------|-----|------|
| 200 | OK | 成功 |
| 400 | 参数错误 | 请求参数错误 |
| 401 | 未登录 | 未登录或Token过期 |
| 403 | 无权限/权限错误 | 无权限访问 |
| 404 | - | 资源不存在 |
