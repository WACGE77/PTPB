from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.db.models import Q
from rest_framework_simplejwt.tokens import AccessToken

from Utils.Const import ERRMSG, PERMISSIONS
from audit.Logging import OperaLogging
from perm.models import ResourceGroupAuth
from rbac.models import User
from resource.models import Resource, Voucher
from terminal.protocol import AsyncSSHClient
from terminal.serialization import SSHAuthSerializer


class SSHConsumer(AsyncWebsocketConsumer):
    resource_permission = PERMISSIONS.RESOURCE.SELF.READ
    voucher_permission = PERMISSIONS.RESOURCE.VOUCHER.READ
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = None
        self.resource = None
        self.voucher = None
        self.pty = None

    @database_sync_to_async
    def auth(self,params):
        serializer = SSHAuthSerializer(data=params)
        if not serializer.is_valid():
            return False,serializer.errors
        self.resource = Resource.objects.get(id=serializer.validated_data['resource'])
        self.voucher = Voucher.objects.get(id=serializer.validated_data['voucher'])
        if self.resource.group != self.voucher.group:
            return False,ERRMSG.ERROR.ARG
        token_str = serializer.validated_data['token']
        try:
            token = AccessToken(token_str)
            pk = token.payload['user_id']
            user = User.objects.get(pk=pk)
        except Exception:
            return False,ERRMSG.ERROR.PERMISSION
        group = self.resource.group
        query = set(ResourceGroupAuth.objects.filter(
            Q(permission__code=self.resource_permission) | Q(permission__code=self.voucher_permission),
            group_id=group,
            role__in = user.roles.all()
        ))
        if len(query) != 2:
            return False,ERRMSG.ERROR.PERMISSION
        return True,None

    async def pty_connect(self):
        self.pty = AsyncSSHClient()
        host = self.resource.ipv4_address or self.resource.ipv6_address
        password_mode = self.voucher.password or None
        try:
            if password_mode:
                await self.pty.connect(host, username=self.voucher.username, password=self.voucher.password,
                                       port=self.resource.port)
            else:
                pass
        except Exception:
            return False,ERRMSG.TIMEOUT.CONNECT
        return True,None


    @database_sync_to_async
    def session_log(self,user,ip,resource,voucher,status,log = None):
        return OperaLogging.session(user,ip,resource,voucher,status,log)

    async def disable(self,msg):
        await self.send(msg)
        await self.close()

    async def connect(self):
        params = self.scope['url_route']['kwargs']
        auth,msg = self.auth(params)
        await self.accept()
        if not auth:
            await self.disable(msg)
            return
        conned,msg = self.pty_connect()
        if not conned:
            await self.disable(msg)
            return

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data=None, bytes_data=None):
        pass

# import asyncio
# import json
# from django.utils import timezone
# from rbac.models import User
# from resource.models import Resource,ResourceVoucher
# from perm.models import BaseAuth,ResourceAuth,ResourceVoucherAuth
from channels.generic.websocket import AsyncWebsocketConsumer
# from rest_framework_simplejwt.tokens import AccessToken
# from channels.db import database_sync_to_async
# from .protocol import AsyncSSHClient
# from audit.Logging import OperaLogging
# from .utils import get_ws_client_ip
# class SSHConsumer(AsyncWebsocketConsumer):
#     #ws://106.13.85.137:8000/api/terminal/ssh/
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.handele = None
#         self.session = None
#         self.connected_flag = False
#         self.log = None
#         self.ip = None
#         self.resource = None
#         self.voucher = None
#         self.queue = asyncio.Queue()
#
#     async def close(self):
#         if self.session:
#             self.session.close()
#         if self.handele:
#             self.handle.cancel()
#         await super().close()
#
#     async def connect(self):
#         self.ip = get_ws_client_ip(self.scope)
#         self.handle = asyncio.create_task(self._data_handle())
#         await self.accept()
#
#     async def disconnect(self, code):
#         try:
#             if self.connected_flag:
#                 self.log.end_time = timezone.now()
#                 await self.session_log(self.user,self.ip,self.resource,self.voucher,"close",self.log)
#             else:
#                 await self.session_log(self.user,self.ip,self.resource,self.voucher,"faild")
#         except Exception:
#             pass
#         return await super().disconnect(code)
#
#     async def receive(self,text_data):
#         try:
#             data = json.loads(text_data)
#         except Exception:
#             await self.send("传参错误,请重试")
#             return
#         await self.queue.put(data)
#
#
#
#     async def _data_handle(self):
#         try:
#             while True:
#                 item = await self.queue.get()
#                 type_ = item.get('type',None)
#                 data = item.get('data')
#                 # print(type_)
#                 # print(data)
#                 # print('--------------------------------------------')
#                 if type_ == 0 and not self.session:
#                     try:
#                         await self.shellInit(data)
#                     except Exception as e:
#                         await self.send(f"连接失败:{str(e)}")
#                         self.close()
#                         return
#                 elif type_ == 1:
#                     await self.session.resize(cols=data.get('cols'),rows=data.get('rows'))
#                 elif type_ == 2:
#                     await self.session.send(data)
#
#         except asyncio.CancelledError:
#             while not self.queue.empty():
#                 try:
#                     item = self.queue.get_nowait()
#                     self.queue.task_done()
#                 except asyncio.QueueEmpty:
#                     break
#         finally:
#             self.handele = None
#
#
#
#     async def shellInit(self,data):
#         token = data.get('token')
#         resource_id = data.get('resource_id')
#         voucher_id = data.get('voucher_id')
#         if not all([token,resource_id,voucher_id]):
#             self.close()
#             return
#         if await self.auth(token,resource_id,voucher_id):
#             await self.create_session(self.resource,self.voucher)
#
#     async def resize(self,option):
#         await self.session.resize(cols=option.get('cols'),rows=option.get('rows'))
#
#     async def create_session(self,resource,voucher):
#         hostname = resource.ipv4_address if resource.ipv4_address else resource.ipv6_address
#         username = voucher.username
#         password = voucher.password
#         port = getattr(resource, 'port', 22)
#         self.session = AsyncSSHClient()
#         self.session.set_recv_callback(self.send)
#         self.session.set_on_disconnect(self.close)
#         await self.session.connect(
#             hostname=hostname,
#             username=username,
#             password=password,
#             port=port,
#             timeout=10,
#             delay=0.5
#         )
#         self.connected_flag = True
#         self.log = await self.session_log(self.user,self.ip,self.resource,self.voucher,"active")
#
#     async def auth(self,token,resource_id,voucher_id):
#         user_id = await self._verify_token(token)
#         has_perm,self.user,self.resource,self.voucher = await self._check_permissions(user_id, resource_id, voucher_id)
#         return has_perm
#
#     @database_sync_to_async
#     def _verify_token(self, token_str):
#         """同步方法：验证 JWT 并返回 user_id"""
#         try:
#             access = AccessToken(token_str)
#             return access.payload["user_id"]
#         except Exception:
#             raise ValueError("token错误")
#
#     @database_sync_to_async
#     def _check_permissions(self, user_id, resource_id, voucher_id):
#         """同步方法：执行所有 ORM 查询和权限判断"""
#         try:
#             user = User.objects.get(id=user_id)
#             resource = Resource.objects.get(id=resource_id)
#             voucher = ResourceVoucher.objects.get(id=voucher_id)
#             roles = user.roles.all()
#             # 资源权限
#             resource_perm = (
#                 BaseAuth.objects.filter(role__in=roles, permission__code='resource.self.read').exists() or
#                 ResourceAuth.objects.filter(role__in=roles, permission__code='resource.self.read', resource=resource).exists() or
#                 ResourceAuth.objects.filter(user=user, permission__code='resource.self.read', resource=resource).exists()
#             )
#             # 凭证权限
#             voucher_perm = (
#                 BaseAuth.objects.filter(role__in=roles, permission__code='resource.voucher.read').exists() or
#                 ResourceVoucherAuth.objects.filter(role__in=roles, permission__code='resource.voucher.read', voucher=voucher).exists() or
#                 ResourceVoucherAuth.objects.filter(user=user, permission__code='resource.voucher.read', voucher=voucher).exists()
#             )
#             return resource_perm and voucher_perm,user,resource,voucher
#
#         except Exception:
#             return None
#
