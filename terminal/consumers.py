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


class BaseConsumer(AsyncWebsocketConsumer):
    """消费者基类，包含SSH和RDP消费者的共同逻辑"""
    
    resource_permission = PERMISSIONS.RESOURCE.SELF.READ
    voucher_permission = PERMISSIONS.RESOURCE.VOUCHER.READ
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = None
        self.ip = None
        self.resource = None
        self.voucher = None
        self.client = None
        self.handle_task = None
        self.log = None
        self.data_queue = Queue()

    @database_sync_to_async
    def auth(self, params):
        """认证方法，由子类实现"""
        raise NotImplementedError("子类必须实现auth方法")

    async def connect_client(self, recv, disconnect):
        """连接客户端，由子类实现"""
        raise NotImplementedError("子类必须实现connect_client方法")

    async def resize(self, cols, rows):
        """调整窗口大小，由子类实现"""
        raise NotImplementedError("子类必须实现resize方法")

    async def send_data(self, data):
        """发送数据，由子类实现"""
        raise NotImplementedError("子类必须实现send_data方法")

    @database_sync_to_async
    def session_log(self, status):
        """记录会话日志"""
        self.log = OperaLogging.session(self.user, self.ip, self.resource, self.voucher, status, self.log)

    async def disable(self, msg):
        """发送错误消息并关闭连接"""
        await self.send(str(msg))
        await self.close()

    async def handle(self):
        """处理数据队列"""
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
                    await self.send_data(content)
        except asyncio.CancelledError:
            while not self.data_queue.empty():
                try:
                    self.data_queue.get_nowait()
                    self.data_queue.task_done()
                except asyncio.QueueEmpty:
                    break
            await self.session_log('close')

    async def connect(self):
        """处理WebSocket连接"""
        params = parse_qs(self.scope['query_string'].decode('utf-8'))
        # 确保resource和voucher参数是数组
        if 'resource' in params and not isinstance(params['resource'], list):
            params['resource'] = [params['resource']]
        if 'voucher' in params and not isinstance(params['voucher'], list):
            params['voucher'] = [params['voucher']]
        # 处理resource_id和voucher_id参数（向后兼容）
        if 'resource_id' in params:
            params['resource'] = params['resource_id']
        if 'voucher_id' in params:
            params['voucher'] = params['voucher_id']
        self.ip = get_ws_client_ip(self.scope)
        await self.accept()
        auth, msg = await self.auth(params)
        if not auth:
            await self.disable(msg)
            return
        conned, msg = await self.connect_client(self.send, self.close)
        if not conned:
            await self.disable(msg)
            return
        self.handle_task = asyncio.create_task(self.handle())

    async def disconnect(self, close_code):
        """处理WebSocket断开连接"""
        if self.client and self.client.get_status:
            await self.client.close()
        if self.handle_task:
            self.handle_task.cancel()

    async def receive(self, text_data=None, bytes_data=None):
        """处理接收到的数据"""
        try:
            data = json.loads(text_data)
            await self.data_queue.put(data)
        except JSONDecodeError:
            pass


class SSHConsumer(BaseConsumer):
    """SSH消费者"""
    
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

    async def connect_client(self, recv, disconnect):
        self.client = AsyncSSHClient()
        self.client.set_recv_callback(recv)
        self.client.set_on_disconnect(disconnect)
        host = self.resource.ipv4_address or self.resource.ipv6_address
        password_mode = self.voucher.password or None
        try:
            if password_mode:
                # 密码认证
                await self.client.connect(
                    host=host,
                    username=self.voucher.username,
                    port=self.resource.port,
                    password=self.voucher.password
                )
            else:
                # 私钥认证
                await self.client.connect(
                    host=host,
                    username=self.voucher.username,
                    port=self.resource.port,
                    private_key=self.voucher.private_key
                )
        except Exception:
            await self.session_log('filed')
            return False, ERRMSG.TIMEOUT.CONNECT
        await self.session_log('active')
        return True, None

    async def resize(self, cols, rows):
        await self.client.resize(cols, rows)

    async def send_data(self, data):
        await self.client.send(data)


class RDPConsumer(BaseConsumer):
    """RDP消费者"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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

    async def connect_client(self, recv, disconnect):
        self.client = AsyncRDPClient()
        self.client.set_recv_callback(recv)
        self.client.set_on_disconnect(disconnect)
        
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
            await self.client.connect(
                self.guacamole_url,
                token
            )
        except Exception as e:
            await self.session_log('filed')
            return False, str(e)
        await self.session_log('active')
        return True, None

    async def resize(self, cols, rows):
        await self.client.resize(cols, rows)

    async def send_data(self, data):
        await self.client.send(data)
