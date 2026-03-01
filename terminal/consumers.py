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
from terminal.protocol import AsyncSSHClient
from terminal.serialization import SSHAuthSerializer


class SSHConsumer(AsyncWebsocketConsumer):
    resource_permission = PERMISSIONS.RESOURCE.SELF.READ
    voucher_permission = PERMISSIONS.RESOURCE.VOUCHER.READ
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = None
        self.ip = None
        self.resource = None
        self.voucher = None
        self.pty:AsyncSSHClient | None = None
        self.handle_task = None
        self.log = None
        self.data_queue = Queue()

    @database_sync_to_async
    def auth(self,params):
        serializer = SSHAuthSerializer(data=params)
        if not serializer.is_valid():
            return False, serializer.errors
        self.resource = serializer.validated_data['resource'][0]
        self.voucher = serializer.validated_data['voucher'][0]
        if self.resource.group != self.voucher.group:
            return False,ERRMSG.SAME.GROUP
        token_str = params.get('token')
        try:
            token = AccessToken(token_str[0])
            pk = token.payload['user_id']
            self.user = User.objects.get(pk=pk)
        except Exception:
            return False,ERRMSG.ERROR.PERMISSION
        group = self.resource.group
        query = set(ResourceGroupAuth.objects.filter(
            Q(permission__code=self.resource_permission) | Q(permission__code=self.voucher_permission),
            resource_group=group,
            role__in = self.user.roles.all()
        ))
        if len(query) != 2:
            return False,ERRMSG.ERROR.PERMISSION
        return True,None

    async def pty_connect(self,recv,disconnect):
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
            return False,ERRMSG.TIMEOUT.CONNECT
        await self.session_log('active')
        return True,None

    async def resize(self,cols,rows):
        await self.pty.resize(cols,rows)

    @database_sync_to_async
    def session_log(self,status):
        self.log =  OperaLogging.session(self.user,self.ip,self.resource,self.voucher,status,self.log)

    async def disable(self,msg):
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
        auth,msg = await self.auth(params)
        if not auth:
            await self.disable(msg)
            return
        conned,msg = await self.pty_connect(self.send,self.close)
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
            await  self.data_queue.put(data)
        except JSONDecodeError:
            pass
