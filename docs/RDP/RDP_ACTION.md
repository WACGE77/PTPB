# RDP 功能实现操作文档（后端）

## 1. 准备工作

### 1.1 环境要求

- **后端**: Django 5.2 + DRF + Channels
- **RDP协议**: Apache Guacamole
- **WebSocket**: Channels + Daphne
- **认证**: JWT (simplejwt)

### 1.2 依赖安装

```bash
# 安装Django和相关依赖
pip install django djangorestframework channels daphne

# 安装JWT认证
pip install djangorestframework-simplejwt

# 安装数据库依赖
pip install mysqlclient

# 安装其他依赖
pip install django-filter python-jose aiohttp
```

## 2. 后端实现

### 2.1 集成到terminal模块

#### 2.1.1 更新序列化器

```python
# terminal/serialization.py
from rest_framework import serializers
from Utils.Const import ERRMSG
from resource.models import Resource, Voucher

class SSHAuthSerializer(serializers.Serializer):
    resource = serializers.PrimaryKeyRelatedField(
        queryset=Resource.objects.all(),
        error_messages={
            'does_not_exist': ERRMSG.ABSENT.RESOURCE
        },
        many=True,
    )
    voucher = serializers.PrimaryKeyRelatedField(
        queryset=Voucher.objects.all(),
        error_messages={
            'does_not_exist': ERRMSG.ABSENT.VOUCHER
        },
        many = True,
    )
    token = serializers.CharField(read_only=True)

class RDPAuthSerializer(serializers.Serializer):
    resource = serializers.PrimaryKeyRelatedField(
        queryset=Resource.objects.all(),
        error_messages={
            'does_not_exist': ERRMSG.ABSENT.RESOURCE
        },
        many=True,
    )
    voucher = serializers.PrimaryKeyRelatedField(
        queryset=Voucher.objects.all(),
        error_messages={
            'does_not_exist': ERRMSG.ABSENT.VOUCHER
        },
        many = True,
    )
    token = serializers.CharField(read_only=True)
    resolution = serializers.CharField(default='1024x768')
    color_depth = serializers.IntegerField(default=16)
    enable_clipboard = serializers.BooleanField(default=True)
```

#### 2.1.2 更新协议实现

```python
# terminal/protocol.py
import asyncio
import asyncssh
import aiohttp
import json

class AsyncSSHClient:
    def __init__(self):
        self._conn = None
        self._process = None
        self._recv_task = None
        self._lock = asyncio.Lock()
        self._connected = False
        self._on_disconnect = None
        self._recv_callback = None

    async def connect(self, hostname, username, port=22, timeout=10, delay=1,
                      password=None, private_key=None, private_key_password=None):
        """
        建立 SSH 连接，支持密码或私钥认证
        
        Args:
            hostname: 主机地址
            username: 用户名
            port: 端口号，默认为 22
            timeout: 连接超时时间（秒），默认为 10
            delay: 连接失败后的重试延迟（秒），默认为 1
            password: 密码认证方式（与 private_key 二选一）
            private_key: 私钥内容（与 password 二选一）
            private_key_password: 私钥密码（如果私钥有密码保护）
        """
        async with self._lock:
            if self._recv_callback is None:
                raise ValueError("recv_callback is not set. Please call set_recv_callback() first.")
            if self._connected:
                raise ValueError("SSH connection is already active.")
            
            # 验证认证参数
            if password is None and private_key is None:
                raise ValueError("必须提供 password 或 private_key 其中之一")
            if password is not None and private_key is not None:
                raise ValueError("password 和 private_key 不能同时提供")

            try:
                # 根据认证方式构建连接参数
                connect_kwargs = {
                    'hostname': hostname,
                    'port': port,
                    'username': username,
                    'known_hosts': None
                }
                
                if password is not None:
                    # 密码认证
                    connect_kwargs['password'] = password
                else:
                    # 私钥认证
                    connect_kwargs['client_keys'] = [asyncssh.import_private_key(
                        private_key,
                        passphrase=private_key_password
                    )]
                
                self._conn = await asyncio.wait_for(
                    asyncssh.connect(**connect_kwargs),
                    timeout=timeout
                )
                self._process = await self._conn.create_process(
                    term_type='xterm',
                    term_size=(80, 24),
                )
                self._connected = True

                self._recv_task = asyncio.create_task(self._recv_loop())

            except Exception as e:
                self._connected = False
                raise e
    
    async def _recv_loop(self):
        try:
            while self._connected:
                data = await self._process.stdout.read(1024)
                if not data:
                    break
                await self._recv_callback(data)

        except Exception:
            pass
        finally:
            asyncio.create_task(self.close())


    def set_on_disconnect(self,callback):
        self._on_disconnect = callback

    def set_recv_callback(self, callback):
        """设置接收数据的回调函数（必须是普通函数或可调用对象）"""
        self._recv_callback = callback

    async def send(self, data: str):
        if not self._connected or self._process.stdin.is_closing():
            raise ConnectionError("SSH connection is not active.")
        self._process.stdin.write(data)

    @property
    def get_status(self) -> bool:
        return self._connected

    async def resize(self, cols: int, rows: int):
        if not self._process or not self._connected:
            return
        try:
            await self._process.channel.change_terminal_size(
                width=cols,
                height=rows
            )
        except Exception as e:
            pass

    async def close(self):
        async with self._lock:
            if not self._connected:
                return
            self._connected = False
            if self._on_disconnect:
                await self._on_disconnect()
            if self._recv_task and not self._recv_task.done():
                self._recv_task.cancel()
                try:
                    await self._recv_task
                except asyncio.CancelledError:
                    pass
            if self._process:
                self._process.stdin.close()
                self._process.kill()
            if self._conn:
                self._conn.close()
                await self._conn.wait_closed()
            # 清理引用
            self._conn = None
            self._process = None
            self._recv_task = None
            self._recv_callback = None

class AsyncRDPClient:
    def __init__(self):
        self._session = None
        self._websocket = None
        self._connected = False
        self._on_disconnect = None
        self._recv_callback = None
        self._guacamole_url = None

    async def connect(self, guacamole_url, token, timeout=10):
        """
        建立 RDP 连接，通过 Guacamole WebSocket
        
        Args:
            guacamole_url: Guacamole WebSocket URL
            token: JWT 令牌
            timeout: 连接超时时间（秒），默认为 10
        """
        if self._recv_callback is None:
            raise ValueError("recv_callback is not set. Please call set_recv_callback() first.")
        if self._connected:
            raise ValueError("RDP connection is already active.")

        try:
            self._session = aiohttp.ClientSession()
            self._guacamole_url = f"{guacamole_url}?token={token}"
            
            # 连接到 Guacamole WebSocket
            self._websocket = await asyncio.wait_for(
                self._session.ws_connect(self._guacamole_url),
                timeout=timeout
            )
            self._connected = True

            # 启动接收循环
            asyncio.create_task(self._recv_loop())

        except Exception as e:
            self._connected = False
            if self._session:
                await self._session.close()
            raise e

    async def _recv_loop(self):
        try:
            async for msg in self._websocket:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    await self._recv_callback(msg.data)
                elif msg.type == aiohttp.WSMsgType.CLOSED:
                    break
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    break
        except Exception:
            pass
        finally:
            asyncio.create_task(self.close())

    def set_on_disconnect(self, callback):
        self._on_disconnect = callback

    def set_recv_callback(self, callback):
        """设置接收数据的回调函数"""
        self._recv_callback = callback

    async def send(self, data: str):
        if not self._connected or self._websocket.closed:
            raise ConnectionError("RDP connection is not active.")
        await self._websocket.send_str(data)

    @property
    def get_status(self) -> bool:
        return self._connected

    async def resize(self, cols: int, rows: int):
        """
        调整 RDP 会话窗口大小
        
        Args:
            cols: 列数
            rows: 行数
        """
        if not self._connected or self._websocket.closed:
            return
        # 发送 Guacamole 格式的大小调整命令
        resize_command = json.dumps({
            "type": "size",
            "width": cols,
            "height": rows
        })
        await self._websocket.send_str(resize_command)

    async def close(self):
        if not self._connected:
            return
        self._connected = False
        if self._on_disconnect:
            await self._on_disconnect()
        if self._websocket and not self._websocket.closed:
            await self._websocket.close()
        if self._session:
            await self._session.close()
        # 清理引用
        self._session = None
        self._websocket = None
        self._guacamole_url = None
```

#### 2.1.3 更新WebSocket消费者

```python
# terminal/consumers.py
import asyncio
import json
from asyncio import Queue
from json import JSONDecodeError
from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.db.models import Q
from rest_framework_simplejwt.tokens import AccessToken
from Utils.Const import ERRMSG, PERMISSIONS
from Utils.before import get_ws_client_ip
from audit.Logging import OperaLogging
from perm.models import ResourceGroupAuth
from rbac.models import User
from terminal.protocol import AsyncSSHClient, AsyncRDPClient
from terminal.serialization import SSHAuthSerializer, RDPAuthSerializer

class SSHConsumer(AsyncWebsocketConsumer):
    resource_permission = PERMISSIONS.RESOURCE.SELF.READ
    voucher_permission = PERMISSIONS.RESOURCE.VOUCHER.READ
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = None
        self.ip = None
        self.resource = None
        self.voucher = None
        self.pty: AsyncSSHClient | None = None
        self.handle_task = None
        self.log = None
        self.data_queue = Queue()

    @database_sync_to_async
    def auth(self, params):
        serializer = SSHAuthSerializer(data=params)
        if not serializer.is_valid():
            return False, serializer.errors
        self.resource = serializer.validated_data['resource'][0]
        self.voucher = serializer.validated_data['voucher'][0]
        if self.resource.group != self.voucher.group:
            return False, ERRMSG.SAME.GROUP
        token_str = params.get('token')
        try:
            token = AccessToken(token_str[0])
            pk = token.payload['user_id']
            self.user = User.objects.get(pk=pk)
        except Exception:
            return False, ERRMSG.ERROR.PERMISSION
        group = self.resource.group
        query = set(ResourceGroupAuth.objects.filter(
            Q(permission__code=self.resource_permission) | Q(permission__code=self.voucher_permission),
            resource_group=group,
            role__in=self.user.roles.all()
        ))
        if len(query) != 2:
            return False, ERRMSG.ERROR.PERMISSION
        return True, None

    async def pty_connect(self, recv, disconnect):
        self.pty = AsyncSSHClient()
        self.pty.set_recv_callback(recv)
        self.pty.set_on_disconnect(disconnect)
        host = self.resource.ipv4_address or self.resource.ipv6_address
        password_mode = self.voucher.password or None
        try:
            if password_mode:
                # 密码认证
                await self.pty.connect(
                    host,
                    username=self.voucher.username,
                    password=self.voucher.password,
                    port=self.resource.port
                )
            else:
                # 私钥认证
                await self.pty.connect(
                    host,
                    username=self.voucher.username,
                    private_key=self.voucher.private_key,
                    port=self.resource.port
                )
        except Exception:
            await self.session_log('filed')
            return False, ERRMSG.TIMEOUT.CONNECT
        await self.session_log('active')
        return True, None

    async def resize(self, cols, rows):
        await self.pty.resize(cols, rows)

    @database_sync_to_async
    def session_log(self, status):
        self.log = OperaLogging.session(self.user, self.ip, self.resource, self.voucher, status, self.log)

    async def disable(self, msg):
        await self.send(str(msg))
        await self.close()

    async def handle(self):
        try:
            while True:
                data = await self.data_queue.get()
                type_ = data.get('type')
                content = data.get('data')
                if type_ == 1:
                    col = content.get('cols')
                    row = content.get('rows')
                    await self.resize(col, row)
                elif type_ == 2:
                    await self.pty.send(content)
        except asyncio.CancelledError:
            while not self.data_queue.empty():
                try:
                    self.data_queue.get_nowait()
                    self.data_queue.task_done()
                except asyncio.QueueEmpty:
                    break
            await self.session_log('close')

    async def connect(self):
        params = parse_qs(self.scope['query_string'].decode('utf-8'))
        self.ip = get_ws_client_ip(self.scope)
        await self.accept()
        auth, msg = await self.auth(params)
        if not auth:
            await self.disable(msg)
            return
        conned, msg = await self.pty_connect(self.send, self.close)
        if not conned:
            await self.disable(msg)
            return
        self.handle_task = asyncio.create_task(self.handle())

    async def disconnect(self, close_code):
        if self.pty and self.pty.get_status:
            await self.pty.close()
        if self.handle_task:
            self.handle_task.cancel()

    async def receive(self, text_data=None, bytes_data=None):
        try:
            data = json.loads(text_data)
            await self.data_queue.put(data)
        except JSONDecodeError:
            pass

class RDPConsumer(AsyncWebsocketConsumer):
    resource_permission = PERMISSIONS.RESOURCE.SELF.READ
    voucher_permission = PERMISSIONS.RESOURCE.VOUCHER.READ
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = None
        self.ip = None
        self.resource = None
        self.voucher = None
        self.rdp_client: AsyncRDPClient | None = None
        self.handle_task = None
        self.log = None
        self.data_queue = Queue()
        self.guacamole_url = "ws://localhost:8080/guacamole/websocket"
        self.resolution = "1024x768"
        self.color_depth = 16
        self.enable_clipboard = True

    @database_sync_to_async
    def auth(self, params):
        serializer = RDPAuthSerializer(data=params)
        if not serializer.is_valid():
            return False, serializer.errors
        self.resource = serializer.validated_data['resource'][0]
        self.voucher = serializer.validated_data['voucher'][0]
        if self.resource.group != self.voucher.group:
            return False, ERRMSG.SAME.GROUP
        token_str = params.get('token')
        try:
            token = AccessToken(token_str[0])
            pk = token.payload['user_id']
            self.user = User.objects.get(pk=pk)
        except Exception:
            return False, ERRMSG.ERROR.PERMISSION
        group = self.resource.group
        query = set(ResourceGroupAuth.objects.filter(
            Q(permission__code=self.resource_permission) | Q(permission__code=self.voucher_permission),
            resource_group=group,
            role__in=self.user.roles.all()
        ))
        if len(query) != 2:
            return False, ERRMSG.ERROR.PERMISSION
        # 获取RDP配置参数
        self.resolution = serializer.validated_data.get('resolution', "1024x768")
        self.color_depth = serializer.validated_data.get('color_depth', 16)
        self.enable_clipboard = serializer.validated_data.get('enable_clipboard', True)
        return True, None

    async def rdp_connect(self, recv, disconnect):
        self.rdp_client = AsyncRDPClient()
        self.rdp_client.set_recv_callback(recv)
        self.rdp_client.set_on_disconnect(disconnect)
        
        # 生成JWT令牌
        import jwt
        import time
        import uuid
        from BackEnd.settings import SECRET_KEY
        
        session_id = str(uuid.uuid4())
        payload = {
            'user_id': self.user.id,
            'resource_id': self.resource.id,
            'voucher_id': self.voucher.id,
            'session_id': session_id,
            'resolution': self.resolution,
            'color_depth': self.color_depth,
            'enable_clipboard': self.enable_clipboard,
            'exp': int(time.time()) + 3600  # 1小时过期
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
        
        try:
            await self.rdp_client.connect(
                self.guacamole_url,
                token
            )
        except Exception as e:
            await self.session_log('filed')
            return False, str(e)
        await self.session_log('active')
        return True, None

    async def resize(self, cols, rows):
        await self.rdp_client.resize(cols, rows)

    @database_sync_to_async
    def session_log(self, status):
        self.log = OperaLogging.session(self.user, self.ip, self.resource, self.voucher, status, self.log)

    async def disable(self, msg):
        await self.send(str(msg))
        await self.close()

    async def handle(self):
        try:
            while True:
                data = await self.data_queue.get()
                type_ = data.get('type')
                content = data.get('data')
                if type_ == 1:
                    col = content.get('cols')
                    row = content.get('rows')
                    await self.resize(col, row)
                elif type_ == 2:
                    await self.rdp_client.send(content)
        except asyncio.CancelledError:
            while not self.data_queue.empty():
                try:
                    self.data_queue.get_nowait()
                    self.data_queue.task_done()
                except asyncio.QueueEmpty:
                    break
            await self.session_log('close')

    async def connect(self):
        params = parse_qs(self.scope['query_string'].decode('utf-8'))
        self.ip = get_ws_client_ip(self.scope)
        await self.accept()
        auth, msg = await self.auth(params)
        if not auth:
            await self.disable(msg)
            return
        conned, msg = await self.rdp_connect(self.send, self.close)
        if not conned:
            await self.disable(msg)
            return
        self.handle_task = asyncio.create_task(self.handle())

    async def disconnect(self, close_code):
        if self.rdp_client and self.rdp_client.get_status:
            await self.rdp_client.close()
        if self.handle_task:
            self.handle_task.cancel()

    async def receive(self, text_data=None, bytes_data=None):
        try:
            data = json.loads(text_data)
            await self.data_queue.put(data)
        except JSONDecodeError:
            pass
```

#### 2.1.4 更新路由配置

```python
# terminal/urls.py
from django.urls import path
from terminal.consumers import SSHConsumer, RDPConsumer

websocket_urlpatterns = [
    path('ws/ssh/', SSHConsumer.as_asgi()),
    path('ws/rdp/', RDPConsumer.as_asgi()),
]

# BackEnd/urls.py
from django.urls import path, include

urlpatterns = [
    # 其他路由...
    path('terminal/', include('terminal.urls')),
]
```

## 3. 集成测试

### 3.1 测试步骤

1. **启动服务**
   - 启动Django后端服务
   - 启动Guacamole Server

2. **创建测试资源**
   - 创建Windows服务器资源（协议选择RDP）
   - 创建RDP凭证

3. **测试连接**
   - 登录堡垒机
   - 建立WebSocket连接到 `/terminal/ws/rdp/`
   - 测试连接Windows服务器
   - 测试断开连接

4. **测试权限**
   - 创建测试用户
   - 分配不同权限
   - 测试权限控制

5. **测试审计日志**
   - 检查RDP会话日志
   - 验证审计记录

### 3.2 测试用例

| 测试场景 | 预期结果 |
|---------|---------|
| 正常连接 | 成功建立RDP连接，返回远程桌面画面 |
| 断开连接 | 成功断开连接，记录审计日志 |
| 权限不足 | 返回403权限错误 |
| 资源不可达 | 返回连接错误，记录错误日志 |
| 令牌过期 | 返回认证错误 |

## 4. 故障排查

### 4.1 常见问题

| 问题 | 可能原因 | 解决方案 |
|------|---------|---------|
| 连接失败 | Guacamole服务未启动 | 启动guacd服务 |
| 权限错误 | 用户权限不足 | 分配相应的资源和凭证权限 |
| WebSocket错误 | 网络问题或配置错误 | 检查网络连接和配置 |
| 令牌过期 | JWT令牌过期 | 重新建立连接 |
| 资源不可达 | 网络问题或服务器未运行 | 检查网络连接和服务器状态 |

### 4.2 日志查看

```bash
# 查看Django日志
python manage.py runserver 0.0.0.0:8000

# 查看Guacamole日志
tail -f /var/log/guacamole/guacd.log
```

## 5. 总结

通过以上步骤，我们成功在现有的堡垒机项目中集成了Windows远程桌面功能，将RDP集成到terminal模块中，类似于SSH的实现方式。使用Apache Guacamole实现RDP协议解析与Web化远程桌面，无缝对接现有RBAC权限、资源管理、审计日志模块，遵循原有代码规范。

主要实现了以下功能：

1. **集成到terminal模块**: 与SSH实现保持一致的结构
2. **RDP协议支持**: 使用Apache Guacamole实现
3. **WebSocket连接**: 类似于SSH的WebSocket实现
4. **共享资源表**: 直接使用现有的Resource和Voucher模型，避免字段重复
5. **权限控制**: 基于现有RBAC权限体系
6. **审计日志**: 记录RDP会话操作

这样，用户可以通过与SSH相同的方式使用RDP连接Windows服务器，享受统一的终端体验。