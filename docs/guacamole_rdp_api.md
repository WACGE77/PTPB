# Guacamole RDP API 接口文档

本文档描述了Guacamole中与RDP（远程桌面协议）相关的API接口，用于在堡垒机中集成RDP功能。

## 1. 认证接口

### 1.1 获取认证令牌

**请求方法**: POST

**请求URL**: `https://www.wacgee.icu:8888/api/tokens`

**请求参数**:

| 参数名 | 类型 | 必填 | 描述 |
|-------|------|------|------|
| username | string | 是 | 用户名，如 `guacadmin` |
| password | string | 是 | 密码，如 `wen9369494260.0` |

**请求示例**:

```python
import requests

url = "https://www.wacgee.icu:8888/api/tokens"
data = {
    "username": "guacadmin",
    "password": "wen9369494260.0"
}

response = requests.post(url, data=data, verify=False)
token_data = response.json()
token = token_data['authToken']
data_source = token_data['dataSource']
```

**响应示例**:

```json
{
  "authToken": "F52CD7B5722B7EED8A034EA7A83D963144685FED12CD7AF0A54EB88BB110795B",
  "dataSource": "postgresql"
}
```

## 2. 连接管理接口

### 2.1 获取所有连接

**请求方法**: GET

**请求URL**: `https://www.wacgee.icu:8888/api/session/data/{dataSource}/connections?token={token}`

**请求参数**:

| 参数名 | 类型 | 必填 | 描述 |
|-------|------|------|------|
| dataSource | string | 是 | 数据源，如 `postgresql` |
| token | string | 是 | 认证令牌 |

**请求示例**:

```python
import requests

url = f"https://www.wacgee.icu:8888/api/session/data/{data_source}/connections?token={token}"
response = requests.get(url, verify=False)
connections = response.json()
```

**响应示例**:

```json
{
  "4": {
    "name": "测试RDP连接",
    "identifier": "4",
    "parentIdentifier": "ROOT",
    "protocol": "rdp",
    "attributes": {},
    "activeConnections": 0
  }
}
```

### 2.2 创建RDP连接

**请求方法**: POST

**请求URL**: `https://www.wacgee.icu:8888/api/session/data/{dataSource}/connections?token={token}`

**请求参数**:

| 参数名 | 类型 | 必填 | 描述 |
|-------|------|------|------|
| dataSource | string | 是 | 数据源，如 `postgresql` |
| token | string | 是 | 认证令牌 |

**请求体**:

```json
{
  "name": "测试RDP连接",
  "parentIdentifier": "ROOT",
  "protocol": "rdp",
  "attributes": {},
  "parameters": {
    "hostname": "192.168.1.1",
    "port": "3389",
    "username": "testuser",
    "password": "testpassword"
  }
}
```

**请求示例**:

```python
import requests
import json

url = f"https://www.wacgee.icu:8888/api/session/data/{data_source}/connections?token={token}"
headers = {
    "Content-Type": "application/json"
}

connection_data = {
    "name": "测试RDP连接",
    "parentIdentifier": "ROOT",
    "protocol": "rdp",
    "attributes": {},
    "parameters": {
        "hostname": "192.168.1.1",
        "port": "3389"
    }
}

response = requests.post(url, headers=headers, json=connection_data, verify=False)
connection_info = response.json()
connection_id = connection_info['identifier']
```

**响应示例**:

```json
{
  "name": "测试RDP连接",
  "identifier": "4",
  "parentIdentifier": "ROOT",
  "protocol": "rdp",
  "parameters": {
    "hostname": "192.168.1.1",
    "port": "3389"
  },
  "attributes": {},
  "activeConnections": 0
}
```

### 2.3 获取连接配置

**请求方法**: GET

**请求URL**: `https://www.wacgee.icu:8888/api/session/data/{dataSource}/connections/{connectionId}?token={token}`

**请求参数**:

| 参数名 | 类型 | 必填 | 描述 |
|-------|------|------|------|
| dataSource | string | 是 | 数据源，如 `postgresql` |
| connectionId | string | 是 | 连接ID |
| token | string | 是 | 认证令牌 |

**请求示例**:

```python
import requests

url = f"https://www.wacgee.icu:8888/api/session/data/{data_source}/connections/{connection_id}?token={token}"
response = requests.get(url, verify=False)
config = response.json()
```

**响应示例**:

```json
{
  "name": "测试RDP连接",
  "identifier": "4",
  "parentIdentifier": "ROOT",
  "protocol": "rdp",
  "attributes": {
    "guacd-encryption": null,
    "failover-only": null,
    "weight": null,
    "max-connections": null,
    "guacd-hostname": null,
    "guacd-port": null,
    "max-connections-per-user": null
  },
  "activeConnections": 0
}
```

### 2.4 删除连接

**请求方法**: DELETE

**请求URL**: `https://www.wacgee.icu:8888/api/session/data/{dataSource}/connections/{connectionId}?token={token}`

**请求参数**:

| 参数名 | 类型 | 必填 | 描述 |
|-------|------|------|------|
| dataSource | string | 是 | 数据源，如 `postgresql` |
| connectionId | string | 是 | 连接ID |
| token | string | 是 | 认证令牌 |

**请求示例**:

```python
import requests

url = f"https://www.wacgee.icu:8888/api/session/data/{data_source}/connections/{connection_id}?token={token}"
response = requests.delete(url, verify=False)
```

**响应**:
- 成功: 状态码 204 No Content
- 失败: 状态码 404 Not Found 或其他错误码

## 3. WebSocket连接接口

Guacamole使用WebSocket进行实时的远程桌面会话通信。当用户通过浏览器访问RDP连接时，Guacamole会建立WebSocket连接来传输图像、音频和用户输入。

### 3.1 WebSocket连接URL

**WebSocket URL**: `wss://www.wacgee.icu:8888/websocket-tunnel`

### 3.2 WebSocket连接参数

| 参数名 | 类型 | 必填 | 描述 |
|-------|------|------|------|
| token | string | 是 | 认证令牌 |
| connection | string | 是 | 连接ID |
| width | integer | 是 | 屏幕宽度 |
| height | integer | 是 | 屏幕高度 |
| dpi | integer | 否 | 屏幕DPI，默认为96 |
| audio | string | 否 | 音频编码，如"audio/L8"、"audio/L16" |
| video | string | 否 | 视频编码，如"video/websocket" |

### 3.3 WebSocket连接示例

```javascript
// 创建WebSocket连接
const token = "YOUR_AUTH_TOKEN";
const connectionId = "YOUR_CONNECTION_ID";
const width = 1024;
const height = 768;

const wsUrl = `wss://www.wacgee.icu:8888/websocket-tunnel?token=${token}&connection=${connectionId}&width=${width}&height=${height}`;
const ws = new WebSocket(wsUrl);

// 处理WebSocket事件
ws.onopen = function() {
    console.log("WebSocket连接已打开");
};

ws.onmessage = function(event) {
    // 处理从服务器接收的数据
    console.log("收到数据:", event.data);
};

ws.onerror = function(error) {
    console.error("WebSocket错误:", error);
};

ws.onclose = function() {
    console.log("WebSocket连接已关闭");
};

// 发送数据到服务器
function sendData(data) {
    if (ws.readyState === WebSocket.OPEN) {
        ws.send(data);
    }
}
```

### 3.4 WebSocket通信协议

Guacamole的WebSocket通信使用一种特殊的协议，称为Guacamole协议。该协议使用文本格式，每一行代表一个操作或事件。

**常见的Guacamole协议指令**:

| 指令 | 描述 | 示例 |
|------|------|------|
| `size` | 设置屏幕尺寸 | `size:1024x768` |
| `mouse` | 鼠标事件 | `mouse:100,200,0` |
| `key` | 键盘事件 | `key:40,1` |
| `clipboard` | 剪贴板数据 | `clipboard:text/plain;Hello World` |
| `ack` | 确认收到数据 | `ack` |

### 3.5 集成WebSocket的前端示例

```html
<!DOCTYPE html>
<html>
<head>
    <title>Guacamole RDP连接</title>
    <style>
        #display {
            width: 1024px;
            height: 768px;
            border: 1px solid #ccc;
        }
    </style>
</head>
<body>
    <h1>Guacamole RDP连接</h1>
    <div id="display"></div>
    
    <script>
        // 认证令牌和连接ID
        const token = "YOUR_AUTH_TOKEN";
        const connectionId = "YOUR_CONNECTION_ID";
        
        // 创建WebSocket连接
        const wsUrl = `wss://www.wacgee.icu:8888/websocket-tunnel?token=${token}&connection=${connectionId}&width=1024&height=768`;
        const ws = new WebSocket(wsUrl);
        
        // 获取显示元素
        const display = document.getElementById('display');
        
        // 处理WebSocket事件
        ws.onopen = function() {
            console.log("WebSocket连接已打开");
        };
        
        ws.onmessage = function(event) {
            // 处理从服务器接收的数据
            // 这里需要实现Guacamole协议的解析和渲染
            console.log("收到数据:", event.data);
        };
        
        ws.onerror = function(error) {
            console.error("WebSocket错误:", error);
        };
        
        ws.onclose = function() {
            console.log("WebSocket连接已关闭");
        };
        
        // 处理用户输入
        display.addEventListener('mousedown', function(e) {
            // 发送鼠标事件
            const x = e.offsetX;
            const y = e.offsetY;
            ws.send(`mouse:${x},${y},1`);
        });
        
        display.addEventListener('mouseup', function(e) {
            // 发送鼠标事件
            const x = e.offsetX;
            const y = e.offsetY;
            ws.send(`mouse:${x},${y},0`);
        });
        
        display.addEventListener('mousemove', function(e) {
            // 发送鼠标事件
            const x = e.offsetX;
            const y = e.offsetY;
            ws.send(`mouse:${x},${y},0`);
        });
        
        window.addEventListener('keydown', function(e) {
            // 发送键盘事件
            ws.send(`key:${e.keyCode},1`);
        });
        
        window.addEventListener('keyup', function(e) {
            // 发送键盘事件
            ws.send(`key:${e.keyCode},0`);
        });
    </script>
</body>
</html>
```

## 4. RDP连接参数

RDP连接支持以下参数：

| 参数名 | 描述 | 示例值 |
|-------|------|--------|
| hostname | 目标主机名或IP地址 | 192.168.1.1 |
| port | RDP端口 | 3389 |
| username | 登录用户名 | testuser |
| password | 登录密码 | testpassword |
| domain | 域名 | example.com |
| security | 安全级别 | nla, tls, rdp |
| ignore-cert | 是否忽略证书错误 | true, false |
| resolution | 分辨率 | 1024x768 |
| color-depth | 颜色深度 | 8, 16, 24, 32 |
| console | 是否连接到控制台 | true, false |
| server-layout | 键盘布局 | en-us-qwerty |

## 5. 错误处理

API返回的错误格式如下：

```json
{
  "message": "错误信息",
  "translatableMessage": {
    "key": "APP.TEXT_UNTRANSLATED",
    "variables": {
      "MESSAGE": "错误信息"
    }
  },
  "statusCode": null,
  "expected": null,
  "patches": null,
  "type": "错误类型"
}
```

常见错误类型：
- PERMISSION_DENIED: 权限不足
- BAD_REQUEST: 请求参数错误
- INTERNAL_ERROR: 服务器内部错误
- NOT_FOUND: 资源不存在

## 6. 完整示例

以下是一个完整的示例，展示如何使用Guacamole API管理RDP连接：

```python
import requests
import json

# 禁用SSL警告
requests.packages.urllib3.disable_warnings()

# Guacamole服务器信息
BASE_URL = "https://www.wacgee.icu:8888"
USERNAME = "guacadmin"
PASSWORD = "wen9369494260.0"

def login():
    """登录到Guacamole并获取令牌"""
    url = f"{BASE_URL}/api/tokens"
    data = {
        "username": USERNAME,
        "password": PASSWORD
    }
    
    response = requests.post(url, data=data, verify=False)
    if response.status_code == 200:
        token_data = response.json()
        return token_data
    else:
        print(f"登录失败: {response.status_code} - {response.text}")
        return None

def create_rdp_connection(token_data, name, hostname, port=3389, username="", password=""):
    """创建RDP连接"""
    token = token_data['authToken']
    data_source = token_data.get('dataSource', 'postgresql')
    
    url = f"{BASE_URL}/api/session/data/{data_source}/connections?token={token}"
    headers = {
        "Content-Type": "application/json"
    }
    
    connection_data = {
        "name": name,
        "parentIdentifier": "ROOT",
        "protocol": "rdp",
        "attributes": {},
        "parameters": {
            "hostname": hostname,
            "port": str(port),
            "username": username,
            "password": password
        }
    }
    
    response = requests.post(url, headers=headers, json=connection_data, verify=False)
    if response.status_code == 200:
        connection_info = response.json()
        return connection_info['identifier']
    else:
        print(f"创建RDP连接失败: {response.status_code} - {response.text}")
        return None

def delete_connection(token_data, connection_id):
    """删除连接"""
    token = token_data['authToken']
    data_source = token_data.get('dataSource', 'postgresql')
    
    url = f"{BASE_URL}/api/session/data/{data_source}/connections/{connection_id}?token={token}"
    
    response = requests.delete(url, verify=False)
    return response.status_code == 204

def main():
    # 登录获取令牌
    token_data = login()
    if not token_data:
        return
    
    # 创建RDP连接
    connection_id = create_rdp_connection(
        token_data, 
        "测试RDP连接", 
        "192.168.1.1", 
        3389, 
        "testuser", 
        "testpassword"
    )
    
    if connection_id:
        print(f"创建RDP连接成功，ID: {connection_id}")
        
        # 删除连接
        if delete_connection(token_data, connection_id):
            print("删除RDP连接成功")
        else:
            print("删除RDP连接失败")

if __name__ == "__main__":
    main()
```

## 7. 注意事项

1. 所有API请求都需要在URL中传递认证令牌 `token`
2. 数据源 `dataSource` 从登录响应中获取，通常为 `postgresql` 或 `mysql`
3. 创建RDP连接时，`parentIdentifier` 通常设置为 `ROOT`
4. RDP连接参数根据实际需求进行配置
5. 错误处理非常重要，需要捕获并处理可能的错误
6. 生产环境中应启用SSL验证，本示例中为了简化测试而禁用
7. WebSocket连接需要在前端实现Guacamole协议的解析和渲染

## 8. 集成建议

在堡垒机中集成Guacamole的RDP功能时，建议：

1. 实现统一的认证机制，使用Guacamole的令牌系统
2. 为每个用户创建对应的RDP连接配置
3. 提供友好的界面用于管理RDP连接
4. 实现连接状态监控和日志记录
5. 考虑使用Guacamole的连接共享功能，实现多人协作
6. 使用WebSocket实现实时的远程桌面会话
7. 集成Guacamole的前端库，简化WebSocket通信的实现

通过以上API，您可以在堡垒机中完整集成Guacamole的RDP功能，为用户提供安全、便捷的远程桌面访问能力。