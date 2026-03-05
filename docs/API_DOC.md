# PTPB 堡垒机后端接口文档

## 基础信息

- **基础URL**: `https://设备/api/`
- **WebSocket**: `ws://设备/api/terminal/`
- **认证方式**: JWT Token
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

## 一、认证接口 (rbac)

### 1. 登录接口
- **请求方法**: POST
- **URL**: `https://设备/api/rbac/login/`
- **请求头**: `Content-Type: application/json`

#### 参数说明
| 字段 | 是否必须 | 数据类型 | 备注 |
|------|---------|---------|------|
| account | 是 | 字符串 | 用户账户号用于登录 |
| password | 是 | 字符串 | 用户密码用于登录 |

#### 请求示例
```json
{
    "account": "administrator",
    "password": "administrator"
}
```

#### 返回说明
| 字段 | 说明 |
|------|------|
| code | 状态码 |
| msg | 消息 |
| token.access | 短期token，用于api认证 |
| token.refresh | 长期token，用于刷新短期token |

#### 返回示例
- **成功时返回**
```json
{
    "code": 200,
    "msg": "OK",
    "token": {
        "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzg4MDY4MTgzLCJpYXQiOjE3NzA3ODgxODMsImp0aSI6ImE0MDc5Mzg2Mjg4NTQ0NTBhYWMxM2M1ZjY2ODQxMzRkIiwidXNlcl9pZCI6IjEifQ.y1iMBj0yr-NC9KEdB86_-TYvugj01zIZmL64Rz9Ir0s",
        "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoicmVmcmVzaCIsImV4cCI6MTc3MTM5Mjk4MywiaWF0IjoxNzcwNzg4MTgzLCJqdGkiOiI5MTFiMzIwMjg4Njg0NmYyODM3NWIxNzNmZjYyY2ZkZCIsInVzZXJfaWQiOiIxIn0.KtScOFbvP2q6MekeTL2LEFn0fO7r6RdhQEMOva9xDrA"
    }
}
```

- **异常时返回**
```json
{
    "code": 401,
    "msg": "未登录",
    "detail": "密码错误"
}
```

### 2. 用户登出
- **请求方法**: POST
- **URL**: `https://设备/api/rbac/logout/`
- **请求头**: `Authorization: <access_token>`

#### 请求示例
```
POST https://设备/api/rbac/logout/
Authorization: <access_token>
```

#### 返回说明
| 字段 | 说明 |
|------|------|
| code | 状态码 |
| msg | 消息 |

#### 返回示例
- **成功时返回**
```json
{
    "code": 200,
    "msg": "OK"
}
```

- **异常时返回**
```json
{
    "detail": "未登录"
}
```

### 3. 刷新Token
- **请求方法**: POST
- **URL**: `https://设备/api/rbac/refresh/`
- **Cookie**: `refresh=<refresh_token>`

#### 请求示例
```
POST https://设备/api/rbac/refresh/
Cookie: refresh=<refresh_token>
```

#### 返回说明
| 字段 | 说明 |
|------|------|
| code | 状态码 |
| msg | 消息 |
| token.access | 短期token，用于api认证 |
| token.refresh | 长期token，用于刷新短期token |

#### 返回示例
- **成功时返回**
```json
{
    "code": 200,
    "msg": "OK",
    "token": {
        "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzg4MDY4MTgzLCJpYXQiOjE3NzA3ODgxODMsImp0aSI6ImE0MDc5Mzg2Mjg4NTQ0NTBhYWMxM2M1ZjY2ODQxMzRkIiwidXNlcl9pZCI6IjEifQ.y1iMBj0yr-NC9KEdB86_-TYvugj01zIZmL64Rz9Ir0s",
        "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoicmVmcmVzaCIsImV4cCI6MTc3MTM5Mjk4MywiaWF0IjoxNzcwNzg4MTgzLCJqdGkiOiI5MTFiMzIwMjg4Njg0NmYyODM3NWIxNzNmZjYyY2ZkZCIsInVzZXJfaWQiOiIxIn0.KtScOFbvP2q6MekeTL2LEFn0fO7r6RdhQEMOva9xDrA"
    }
}
```

- **异常时返回**
```json
{
    "code": 400,
    "msg": "参数错误"
}
```

## 二、用户管理 (rbac)

### 4. 添加用户
- **请求方法**: POST
- **URL**: `https://设备/api/rbac/user/add/`
- **请求头**: `Authorization: <access_token>`
- **请求头**: `Content-Type: application/json`

#### 参数说明
| 字段 | 是否必须 | 数据类型 | 备注 |
|------|---------|---------|------|
| account | 是 | 字符串 | 用户账户 |
| password | 是 | 字符串 | 用户密码 |
| name | 是 | 字符串 | 用户昵称 |
| email | 否 | 字符串 | 用户邮箱 |
| status | 是 | 布尔值 | 用户状态 |
| phone_number | 否 | 字符串 | 用户电话 |
| remark | 否 | 字符串 | 备注 |

#### 请求示例
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

#### 返回说明
| 字段 | 说明 |
|------|------|
| code | 状态码 |
| msg | 消息 |

#### 返回示例
- **成功时返回**
```json
{
    "code": 200,
    "msg": "OK"
}
```

- **异常时返回**
```json
{
    "code": 400,
    "msg": "参数错误",
    "detail": {
        "account": ["账户以被注册"]
    }
}
```

### 5. 修改用户
- **请求方法**: POST
- **URL**: `https://设备/api/rbac/user/edit/`
- **请求头**: `Authorization: <access_token>`
- **请求头**: `Content-Type: application/json`

#### 参数说明
| 字段 | 是否必须 | 数据类型 | 备注 |
|------|---------|---------|------|
| id | 是 | 整数 | 用户ID |
| email | 否 | 字符串 | 用户邮箱 |
| name | 否 | 字符串 | 用户昵称 |
| phone_number | 否 | 字符串 | 用户电话 |
| remark | 否 | 字符串 | 备注 |

#### 请求示例
```json
{
    "id": 12,
    "email": "example@test.com",
    "name": "test111",
    "phone_number": "17531333029",
    "remark": "备注"
}
```

#### 返回说明
| 字段 | 说明 |
|------|------|
| code | 状态码 |
| msg | 消息 |

#### 返回示例
- **成功时返回**
```json
{
    "code": 200,
    "msg": "OK"
}
```

- **异常时返回**
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

### 6. 删除用户
- **请求方法**: POST
- **URL**: `https://设备/api/rbac/user/del/`
- **请求头**: `Authorization: <access_token>`
- **请求头**: `Content-Type: application/json`

#### 参数说明
| 字段 | 是否必须 | 数据类型 | 备注 |
|------|---------|---------|------|
| id_list | 是 | 数组 | 用户ID列表 |

#### 请求示例
```json
{
    "id_list": [1, 2]
}
```

#### 返回说明
| 字段 | 说明 |
|------|------|
| code | 状态码 |
| msg | 消息 |

#### 返回示例
- **成功时返回**
```json
{
    "code": 200,
    "msg": "OK"
}
```

- **异常时返回**
```json
{
    "code": 400,
    "msg": "参数错误",
    "detail": "用户受保护,或对象不存在"
}
```

### 7. 查看用户
- **请求方法**: GET
- **URL**: `https://设备/api/rbac/user/get/`
- **请求头**: `Authorization: <access_token>`

#### 查询参数
| 参数 | 类型 | 说明 |
|------|------|------|
| page_size | int | 每页数量 (默认10, 最大100) |
| name | string | 用户名搜索 |
| account | string | 账号搜索 |
| status | bool | 状态过滤 |

#### 请求示例
```
GET https://设备/api/rbac/user/get/?page_size=2&name=tes
Authorization: <access_token>
```

#### 返回说明
| 字段 | 说明 |
|------|------|
| code | 状态码 |
| msg | 消息 |
| total | 总记录数 |
| detail | 用户列表 |

#### 返回示例
- **成功时返回**
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

### 8. 重置自身密码
- **请求方法**: POST
- **URL**: `https://设备/api/rbac/user/reset_password/`
- **请求头**: `Authorization: <access_token>`
- **请求头**: `Content-Type: application/json`

#### 参数说明
| 字段 | 是否必须 | 数据类型 | 备注 |
|------|---------|---------|------|
| old_password | 是 | 字符串 | 旧密码 |
| new_password | 是 | 字符串 | 新密码 |

#### 请求示例
```json
{
    "old_password": "administrator",
    "new_password": "admin123"
}
```

#### 返回说明
| 字段 | 说明 |
|------|------|
| code | 状态码 |
| msg | 消息 |

#### 返回示例
- **成功时返回**
```json
{
    "code": 200,
    "msg": "OK"
}
```

- **异常时返回**
```json
{
    "code": 400,
    "msg": "参数错误",
    "detail": {
        "new_password": ["新旧密码不能相同"]
    }
}
```

### 9. 查询自身信息
- **请求方法**: GET
- **URL**: `https://设备/api/rbac/user/detail/`
- **请求头**: `Authorization: <access_token>`

#### 请求示例
```
GET https://设备/api/rbac/user/detail/
Authorization: <access_token>
```

#### 返回说明
| 字段 | 说明 |
|------|------|
| code | 状态码 |
| msg | 消息 |
| detail | 用户信息 |

#### 返回示例
- **成功时返回**
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

### 10. 绑定用户角色
- **请求方法**: POST
- **URL**: `https://设备/api/rbac/user/role/`
- **请求头**: `Authorization: <access_token>`
- **请求头**: `Content-Type: application/json`

#### 参数说明
| 字段 | 是否必须 | 数据类型 | 备注 |
|------|---------|---------|------|
| id | 是 | 整数 | 用户ID |
| roles | 是 | 数组 | 角色ID列表 |

#### 请求示例
```json
{
    "id": 1,
    "roles": [1]
}
```

#### 返回说明
| 字段 | 说明 |
|------|------|
| code | 状态码 |
| msg | 消息 |

#### 返回示例
- **成功时返回**
```json
{
    "code": 200,
    "msg": "OK"
}
```

- **异常时返回**
```json
{
    "code": 400,
    "msg": "参数错误",
    "detail": "无法操作系统保留项"
}
```

## 三、角色管理 (rbac)

### 11. 添加角色
- **请求方法**: POST
- **URL**: `https://设备/api/rbac/role/add/`
- **请求头**: `Authorization: <access_token>`
- **请求头**: `Content-Type: application/json`

#### 参数说明
| 字段 | 是否必须 | 数据类型 | 备注 |
|------|---------|---------|------|
| name | 是 | 字符串 | 角色名称 |
| code | 是 | 字符串 | 角色编码 |
| description | 否 | 字符串 | 角色描述 |

#### 请求示例
```json
{
    "name": "test",
    "code": "test",
    "description": "测试"
}
```

#### 返回说明
| 字段 | 说明 |
|------|------|
| code | 状态码 |
| msg | 消息 |

#### 返回示例
- **成功时返回**
```json
{
    "code": 200,
    "msg": "OK"
}
```

- **异常时返回**
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

### 12. 修改角色
- **请求方法**: POST
- **URL**: `https://设备/api/rbac/role/edit/`
- **请求头**: `Authorization: <access_token>`
- **请求头**: `Content-Type: application/json`

#### 参数说明
| 字段 | 是否必须 | 数据类型 | 备注 |
|------|---------|---------|------|
| id | 是 | 整数 | 角色ID |
| name | 否 | 字符串 | 角色名称 |
| code | 否 | 字符串 | 角色编码 |
| description | 否 | 字符串 | 角色描述 |

#### 请求示例
```json
{
    "id": 2,
    "name": "test21",
    "code": "test111",
    "description": "测试"
}
```

#### 返回说明
| 字段 | 说明 |
|------|------|
| code | 状态码 |
| msg | 消息 |

#### 返回示例
- **成功时返回**
```json
{
    "code": 200,
    "msg": "OK"
}
```

- **异常时返回**
```json
{
    "code": 400,
    "msg": "参数错误",
    "detail": "无法操作系统保留项"
}
```

### 13. 删除角色
- **请求方法**: POST
- **URL**: `https://设备/api/rbac/role/del/`
- **请求头**: `Authorization: <access_token>`
- **请求头**: `Content-Type: application/json`

#### 参数说明
| 字段 | 是否必须 | 数据类型 | 备注 |
|------|---------|---------|------|
| id_list | 是 | 数组 | 角色ID列表 |

#### 请求示例
```json
{
    "id_list": [1, 2]
}
```

#### 返回说明
| 字段 | 说明 |
|------|------|
| code | 状态码 |
| msg | 消息 |
| total | 删除数量 |

#### 返回示例
- **成功时返回**
```json
{
    "code": 200,
    "msg": "OK",
    "total": 1
}
```

- **异常时返回**
```json
{
    "code": 400,
    "msg": "参数错误",
    "detail": "角色受保护,或对象不存在"
}
```

### 14. 查看角色
- **请求方法**: GET
- **URL**: `https://设备/api/rbac/role/get/`
- **请求头**: `Authorization: <access_token>`

#### 查询参数
| 参数 | 类型 | 说明 |
|------|------|------|
| page_size | int | 每页数量 (默认10, 最大100) |
| all | bool | 获取全部数据 |
| name | string | 角色名称搜索 |

#### 请求示例
```
GET https://设备/api/rbac/role/get/?page_size=1&all=true&name=管
Authorization: <access_token>
```

#### 返回说明
| 字段 | 说明 |
|------|------|
| code | 状态码 |
| msg | 消息 |
| total | 总记录数 |
| detail | 角色列表 |

#### 返回示例
- **成功时返回**
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

### 15. 查看角色系统权限
- **请求方法**: GET
- **URL**: `https://设备/api/rbac/role/get/permission/`
- **请求头**: `Authorization: <access_token>`

#### 查询参数
| 参数 | 类型 | 说明 |
|------|------|------|
| id | int | 角色ID |

#### 请求示例
```
GET https://设备/api/rbac/role/get/permission/?id=1
Authorization: <access_token>
```

#### 返回说明
| 字段 | 说明 |
|------|------|
| code | 状态码 |
| msg | 消息 |
| detail | 角色权限信息 |

#### 返回示例
- **成功时返回**
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

- **异常时返回**
```json
{
    "detail": "未找到。"
}
```

### 16. 授权角色系统权限
- **请求方法**: POST
- **URL**: `https://设备/api/rbac/role/edit/permission/`
- **请求头**: `Authorization: <access_token>`
- **请求头**: `Content-Type: application/json`

#### 参数说明
| 字段 | 是否必须 | 数据类型 | 备注 |
|------|---------|---------|------|
| id | 是 | 整数 | 角色ID |
| perms | 是 | 数组 | 权限ID列表 |

#### 请求示例
```json
{
    "id": 5,
    "perms": [1, 2, 3, 4, 5, 6, 7, 8, 9]
}
```

#### 返回说明
| 字段 | 说明 |
|------|------|
| code | 状态码 |
| msg | 消息 |

#### 返回示例
- **成功时返回**
```json
{
    "code": 200,
    "msg": "OK"
}
```

- **异常时返回**
```json
{
    "code": 400,
    "msg": "参数错误",
    "detail": {
        "perms": ["权限错误"]
    }
}
```

### 17. 获取权限列表
- **请求方法**: GET
- **URL**: `https://设备/api/rbac/perm/`
- **请求头**: `Authorization: <access_token>`

#### 请求示例
```
GET https://设备/api/rbac/perm/
Authorization: <access_token>
```

#### 返回说明
| 字段 | 说明 |
|------|------|
| code | 状态码 |
| msg | 消息 |
| detail | 权限列表 |

#### 返回示例
- **成功时返回**
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

## 四、资源组权限管理 (perm)

### 18. 查看角色资源组权限
- **请求方法**: GET
- **URL**: `https://设备/api/perm/group-auth/get/`
- **请求头**: `Authorization: <access_token>`

#### 查询参数
| 参数 | 类型 | 说明 |
|------|------|------|
| role_id | int | 角色ID |

#### 请求示例
```
GET https://设备/api/perm/group-auth/get/?role_id=1
Authorization: <access_token>
```

#### 返回说明
| 字段 | 说明 |
|------|------|
| code | 状态码 |
| msg | 消息 |
| detail | 角色资源组权限列表 |

#### 返回示例
- **成功时返回**
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

- **异常时返回**
```json
{
    "detail": "未找到。"
}
```

### 19. 授权角色资源组权限
- **请求方法**: POST
- **URL**: `https://设备/api/perm/group-auth/edit/`
- **请求头**: `Authorization: <access_token>`
- **请求头**: `Content-Type: application/json`

#### 参数说明
| 字段 | 是否必须 | 数据类型 | 备注 |
|------|---------|---------|------|
| role_id | 是 | 整数 | 角色ID |
| groups | 是 | 数组 | 资源组权限列表 |

#### 请求示例
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

#### 说明
- permission数组内的值为权限ID，范围16-23

#### 返回说明
| 字段 | 说明 |
|------|------|
| code | 状态码 |
| msg | 消息 |

#### 返回示例
- **成功时返回**
```json
{
    "code": 200,
    "msg": "OK"
}
```

- **异常时返回**
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

## 五、资源组管理 (resource)

### 20. 添加资源组
- **请求方法**: POST
- **URL**: `https://设备/api/resource/group/add/`
- **请求头**: `Authorization: <access_token>`
- **请求头**: `Content-Type: application/json`

#### 参数说明
| 字段 | 是否必须 | 数据类型 | 备注 |
|------|---------|---------|------|
| name | 是 | 字符串 | 资源组名称 |
| description | 否 | 字符串 | 资源组描述 |
| parent | 否 | 整数 | 父资源组ID |
| role | 否 | 整数 | 角色ID（顶级组需要） |

#### 说明
- 顶级组不需要 parent，但需要 role
- 子组需要 parent，且需要拥有父级组的资源管理权限

#### 请求示例
```json
{
    "name": "测试组",
    "description": "测试描述",
    "parent": null,
    "role": 1
}
```

#### 返回说明
| 字段 | 说明 |
|------|------|
| code | 状态码 |
| msg | 消息 |

#### 返回示例
- **成功时返回**
```json
{
    "code": 200,
    "msg": "OK"
}
```

- **异常时返回**
```json
{
    "code": 400,
    "msg": "参数错误",
    "detail": {
        "name": ["名称已被占用"]
    }
}
```

### 21. 修改资源组
- **请求方法**: POST
- **URL**: `https://设备/api/resource/group/edit/`
- **请求头**: `Authorization: <access_token>`
- **请求头**: `Content-Type: application/json`

#### 参数说明
| 字段 | 是否必须 | 数据类型 | 备注 |
|------|---------|---------|------|
| id | 是 | 整数 | 资源组ID |
| description | 否 | 字符串 | 资源组描述 |
| name | 否 | 字符串 | 资源组名称 |

#### 请求示例
```json
{
    "id": 3,
    "description": "改了啊,不是摸鱼了"
}
```

#### 返回说明
| 字段 | 说明 |
|------|------|
| code | 状态码 |
| msg | 消息 |

#### 返回示例
- **成功时返回**
```json
{
    "code": 200,
    "msg": "OK"
}
```

- **异常时返回**
```json
{
    "code": 400,
    "msg": "参数错误",
    "detail": "无法操作系统保留项"
}
```

### 22. 删除资源组
- **请求方法**: POST
- **URL**: `https://设备/api/resource/group/del/`
- **请求头**: `Authorization: <access_token>`
- **请求头**: `Content-Type: application/json`

#### 参数说明
| 字段 | 是否必须 | 数据类型 | 备注 |
|------|---------|---------|------|
| id_list | 是 | 数组 | 资源组ID列表 |

#### 请求示例
```json
{
    "id_list": [1, 2]
}
```

#### 返回说明
| 字段 | 说明 |
|------|------|
| code | 状态码 |
| msg | 消息 |

#### 返回示例
- **成功时返回**
```json
{
    "code": 200,
    "msg": "OK"
}
```

- **异常时返回**
```json
{
    "code": 400,
    "msg": "参数错误",
    "detail": "无法操作系统保留项"
}
```

### 23. 查看资源组
- **请求方法**: GET
- **URL**: `https://设备/api/resource/group/get/`
- **请求头**: `Authorization: <access_token>`

#### 请求示例
```
GET https://设备/api/resource/group/get/
Authorization: <access_token>
```

#### 返回说明
| 字段 | 说明 |
|------|------|
| code | 状态码 |
| msg | 消息 |
| total | 总记录数 |
| detail | 资源组列表 |

#### 返回示例
- **成功时返回**
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

- **异常时返回**
```json
{
    "code": 403,
    "msg": "权限错误"
}
```

## 六、资源管理 (resource)

### 24. 添加资源
- **请求方法**: POST
- **URL**: `https://设备/api/resource/resource/add/`
- **请求头**: `Authorization: <access_token>`
- **请求头**: `Content-Type: application/json`

#### 参数说明
| 字段 | 是否必须 | 数据类型 | 备注 |
|------|---------|---------|------|
| name | 是 | 字符串 | 资源名称 |
| ipv4_address | 是 | 字符串 | IPv4地址 |
| group | 是 | 整数 | 资源组ID |
| protocol_ids | 否 | 数组 | 协议ID列表 |
| port | 否 | 整数 | 端口 |
| description | 否 | 字符串 | 描述 |

#### 请求示例
```json
{
    "name": "ptp",
    "ipv4_address": "106.13.85.137",
    "group": 1,
    "protocol_ids": [1, 2]
}
```

#### 返回说明
| 字段 | 说明 |
|------|------|
| code | 状态码 |
| msg | 消息 |

#### 返回示例
- **成功时返回**
```json
{
    "code": 200,
    "msg": "OK"
}
```

- **异常时返回**
```json
{
    "code": 400,
    "msg": "参数错误",
    "detail": {
        "voucher": ["不同系统组,禁止使用"]
    }
}
```

### 25. 修改资源
- **请求方法**: POST
- **URL**: `https://设备/api/resource/resource/edit/`
- **请求头**: `Authorization: <access_token>`
- **请求头**: `Content-Type: application/json`

#### 参数说明
| 字段 | 是否必须 | 数据类型 | 备注 |
|------|---------|---------|------|
| id | 是 | 整数 | 资源ID |
| description | 否 | 字符串 | 描述 |
| name | 否 | 字符串 | 资源名称 |
| ipv4_address | 否 | 字符串 | IPv4地址 |
| port | 否 | 整数 | 端口 |

#### 请求示例
```json
{
    "id": 3,
    "description": "改了啊,不是摸鱼了"
}
```

#### 返回说明
| 字段 | 说明 |
|------|------|
| code | 状态码 |
| msg | 消息 |

#### 返回示例
- **成功时返回**
```json
{
    "code": 200,
    "msg": "OK"
}
```

- **异常时返回**
```json
{
    "detail": "有关联当前组数据,无法切组"
}
```

### 26. 删除资源
- **请求方法**: POST
- **URL**: `https://设备/api/resource/resource/del/`
- **请求头**: `Authorization: <access_token>`
- **请求头**: `Content-Type: application/json`

#### 参数说明
| 字段 | 是否必须 | 数据类型 | 备注 |
|------|---------|---------|------|
| id_list | 是 | 数组 | 资源ID列表 |

#### 请求示例
```json
{
    "id_list": [1, 2]
}
```

#### 返回说明
| 字段 | 说明 |
|------|------|
| code | 状态码 |
| msg | 消息 |

#### 返回示例
- **成功时返回**
```json
{
    "code": 200,
    "msg": "OK"
}
```

- **异常时返回**
```json
{
    "detail": "错误参数"
}
```

### 27. 查看资源
- **请求方法**: GET
- **URL**: `https://设备/api/resource/resource/get/`
- **请求头**: `Authorization: <access_token>`

#### 查询参数
| 参数 | 类型 | 说明 |
|------|------|------|
| page_size | int | 每页数量 (默认10, 最大100) |
| all | bool | 获取全部数据 |
| name | string | 资源名称搜索 |
| group | int | 资源组ID过滤 |

#### 请求示例
```
GET https://设备/api/resource/resource/get/
Authorization: <access_token>
```

#### 返回说明
| 字段 | 说明 |
|------|------|
| code | 状态码 |
| msg | 消息 |
| total | 总记录数 |
| detail | 资源列表 |
| extra | 资源组列表 |

#### 返回示例
- **成功时返回**
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
            "protocols": [1, 2]
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

- **异常时返回**
```json
{
    "code": 403,
    "msg": "权限错误"
}
```

## 七、凭证管理 (resource)

### 28. 添加凭证
- **请求方法**: POST
- **URL**: `https://设备/api/resource/voucher/add/`
- **请求头**: `Authorization: <access_token>`
- **请求头**: `Content-Type: application/json`

#### 参数说明
| 字段 | 是否必须 | 数据类型 | 备注 |
|------|---------|---------|------|
| name | 是 | 字符串 | 凭证名称 |
| username | 是 | 字符串 | 用户名 |
| password | 二选一 | 字符串 | 密码（与private_key二选一） |
| private_key | 二选一 | 字符串 | 私钥（与password二选一） |
| group | 是 | 整数 | 资源组ID |
| description | 否 | 字符串 | 描述 |

#### 注意
- `password` 和 `private_key` 必须二选一

#### 请求示例
```json
{
    "name": "ptp",
    "username": "root",
    "password": "wen9369494260.0",
    "group": 2
}
```

#### 返回说明
| 字段 | 说明 |
|------|------|
| code | 状态码 |
| msg | 消息 |

#### 返回示例
- **成功时返回**
```json
{
    "code": 200,
    "msg": "OK"
}
```

- **异常时返回**
```json
{
    "code": 400,
    "msg": "参数错误",
    "detail": {
        "name": ["名称已被占用"]
    }
}
```

### 29. 修改凭证
- **请求方法**: POST
- **URL**: `https://设备/api/resource/voucher/edit/`
- **请求头**: `Authorization: <access_token>`
- **请求头**: `Content-Type: application/json`

#### 参数说明
| 字段 | 是否必须 | 数据类型 | 备注 |
|------|---------|---------|------|
| id | 是 | 整数 | 凭证ID |
| name | 否 | 字符串 | 凭证名称 |
| username | 否 | 字符串 | 用户名 |
| password | 二选一 | 字符串 | 密码（与private_key二选一） |
| private_key | 二选一 | 字符串 | 私钥（与password二选一） |
| description | 否 | 字符串 | 描述 |
| group | 否 | 整数 | 资源组ID |

#### 注意
- 修改凭证时，`password` 和 `private_key` 必须二选一（如果要修改认证信息）

#### 请求示例
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

#### 返回说明
| 字段 | 说明 |
|------|------|
| code | 状态码 |
| msg | 消息 |

#### 返回示例
- **成功时返回**
```json
{
    "code": 200,
    "msg": "OK"
}
```

- **异常时返回**
```json
{
    "detail": "有关联当前组数据,无法切组"
}
```

### 30. 删除凭证
- **请求方法**: POST
- **URL**: `https://设备/api/resource/voucher/del/`
- **请求头**: `Authorization: <access_token>`
- **请求头**: `Content-Type: application/json`

#### 参数说明
| 字段 | 是否必须 | 数据类型 | 备注 |
|------|---------|---------|------|
| id_list | 是 | 数组 | 凭证ID列表 |

#### 请求示例
```json
{
    "id_list": [1, 2]
}
```

#### 返回说明
| 字段 | 说明 |
|------|------|
| code | 状态码 |
| msg | 消息 |

#### 返回示例
- **成功时返回**
```json
{
    "code": 200,
    "msg": "OK"
}
```

- **异常时返回**
```json
{
    "detail": "错误参数"
}
```

### 31. 查看凭证
- **请求方法**: GET
- **URL**: `https://设备/api/resource/voucher/get/`
- **请求头**: `Authorization: <access_token>`

#### 查询参数
| 参数 | 类型 | 说明 |
|------|------|------|
| page_size | int | 每页数量 (默认10, 最大100) |
| all | bool | 获取全部数据 |
| group | int | 资源组ID过滤 |

#### 请求示例
```
GET https://设备/api/resource/voucher/get/
Authorization: <access_token>
```

#### 返回说明
| 字段 | 说明 |
|------|------|
| code | 状态码 |
| msg | 消息 |
| total | 总记录数 |
| detail | 凭证列表 |

#### 返回示例
- **成功时返回**
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

- **异常时返回**
```json
{
    "code": 403,
    "msg": "权限错误"
}
```

## 八、审计日志 (audit)

### 32. 查看登录日志
- **请求方法**: GET
- **URL**: `https://设备/api/audit/login/get/`
- **请求头**: `Authorization: <access_token>`

#### 查询参数
| 参数 | 类型 | 说明 |
|------|------|------|
| self | bool | 是否只查看自己的日志 |
| desc | bool | 是否降序排列 |
| page_size | int | 每页数量 (默认10, 最大100) |

#### 请求示例
```
GET https://设备/api/audit/login/get/?self=true&desc=true
Authorization: <access_token>
```

#### 返回说明
| 字段 | 说明 |
|------|------|
| code | 状态码 |
| msg | 消息 |
| total | 总记录数 |
| detail | 登录日志列表 |

#### 返回示例
- **成功时返回**
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

- **异常时返回**
```json
{
    "code": 403,
    "msg": "权限错误"
}
```

### 33. 查看操作日志
- **请求方法**: GET
- **URL**: `https://设备/api/audit/opera/get/`
- **请求头**: `Authorization: <access_token>`

#### 查询参数
| 参数 | 类型 | 说明 |
|------|------|------|
| self | bool | 是否只查看自己的日志 |
| operation | string | 操作类型搜索 |
| page_size | int | 每页数量 (默认10, 最大100) |

#### 请求示例
```
GET https://设备/api/audit/opera/get/?self=true&operation=添加
Authorization: <access_token>
```

#### 返回说明
| 字段 | 说明 |
|------|------|
| code | 状态码 |
| msg | 消息 |
| total | 总记录数 |
| detail | 操作日志列表 |

#### 返回示例
- **成功时返回**
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

- **异常时返回**
```json
{
    "code": 403,
    "msg": "权限错误"
}
```

### 34. 查看会话日志
- **请求方法**: GET
- **URL**: `https://设备/api/audit/session/get/`
- **请求头**: `Authorization: <access_token>`

#### 查询参数
| 参数 | 类型 | 说明 |
|------|------|------|
| self | bool | 是否只查看自己的日志 |
| resource | string | 资源名称搜索 |
| page_size | int | 每页数量 (默认10, 最大100) |

#### 请求示例
```
GET https://设备/api/audit/session/get/?self=true&resource=p
Authorization: <access_token>
```

#### 返回说明
| 字段 | 说明 |
|------|------|
| code | 状态码 |
| msg | 消息 |
| total | 总记录数 |
| detail | 会话日志列表 |

#### 返回示例
- **成功时返回**
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

- **异常时返回**
```json
{
    "code": 403,
    "msg": "权限错误"
}
```

## 九、WebSocket 终端连接 (terminal)

### 35. SSH连接
- **WebSocket**: `ws://设备/api/terminal/ssh/`

#### 连接参数 (Query String)
```
ws://设备/api/terminal/ssh/?token=<access_token>&resource_id=1&voucher_id=1
```

#### 消息格式 (客户端 → 服务器)
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

#### 消息格式 (服务器 → 客户端)
- 直接发送终端输出文本

#### 关闭连接
- 发送空消息或关闭WebSocket

### 36. RDP连接
- **WebSocket**: `ws://设备/api/terminal/rdp/`

#### 连接参数 (Query String)
```
ws://设备/api/terminal/rdp/?token=<access_token>&resource_id=1&voucher_id=1&resolution=1024x768&color_depth=16&enable_clipboard=true
```

#### 参数说明
| 字段 | 是否必须 | 数据类型 | 备注 |
|------|---------|---------|------|
| token | 是 | 字符串 | JWT访问令牌 |
| resource_id | 是 | 整数 | 资源ID |
| voucher_id | 是 | 整数 | 凭证ID |
| resolution | 否 | 字符串 | 分辨率，默认1024x768 |
| color_depth | 否 | 整数 | 颜色深度，默认16 |
| enable_clipboard | 否 | 布尔值 | 是否启用剪贴板，默认true |

#### 消息格式 (客户端 → 服务器)
```json
{
    "type": 1,
    "data": {
        "cols": 1024,
        "rows": 768
    }
}
```
- Type 1: 调整窗口大小

```json
{
    "type": 2,
    "data": "<Guacamole协议数据>"
}
```
- Type 2: 发送RDP数据

#### 消息格式 (服务器 → 客户端)
- 直接发送Guacamole协议数据

#### 关闭连接
- 发送空消息或关闭WebSocket

## 十、动态路由 API (rbac)

### 37. 获取动态路由
- **请求方法**: GET
- **URL**: `https://设备/api/rbac/routes/`
- **请求头**: `Authorization: <access_token>`

#### 请求示例
```
GET https://设备/api/rbac/routes/
Authorization: <access_token>
```

#### 返回说明
| 字段 | 说明 |
|------|------|
| code | 状态码 |
| msg | 消息 |
| detail | 路由列表 |

#### 返回示例
- **成功时返回**
```json
{
    "code": 200,
    "msg": "OK",
    "detail": [
        {
            "path": "/overview",
            "component": "@/views/IndexPage.vue",
            "meta": {
                "title": "概览",
                "icon": "Monitor",
                "permission": "system.user.read"
            },
            "children": []
        },
        {
            "path": "permission_manage",
            "component": "",
            "meta": {
                "title": "权限管理",
                "icon": "User",
                "permission": null
            },
            "children": []
        },
        {
            "path": "/audit",
            "component": "@/views/AuditView.vue",
            "meta": {
                "title": "审计日志",
                "icon": "Document",
                "permission": "audit.session.read"
            },
            "children": []
        }
    ]
}
```

- **异常时返回**
```json
{
    "code": 401,
    "msg": "未登录",
    "detail": "未登录或Token过期"
}
```

## 错误码说明

| code | msg | 说明 |
|------|-----|------|
| 200 | OK | 成功 |
| 400 | 参数错误 | 请求参数错误 |
| 401 | 未登录 | 未登录或Token过期 |
| 403 | 无权限/权限错误 | 无权限访问 |
| 404 | - | 资源不存在 |