import asyncio
import json
from asgiref.sync import sync_to_async
from rbac.models import User
from resource.models import Resource,ResourceVoucher
from perm.models import BaseAuth,ResourceAuth,ResourceVoucherAuth
from channels.generic.websocket import AsyncWebsocketConsumer
from rest_framework_simplejwt.tokens import AccessToken
from channels.db import database_sync_to_async
from .protocol import AsyncSSHClient
from audit.Logging import OperaLogging
from .utils import get_ws_client_ip
class SSHConsumer(AsyncWebsocketConsumer):
    #ws://106.13.85.137:8000/api/terminal/ssh/
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_auth = False
        self.session = None
        self.log = None
        self._closed = False
    async def close(self):
        if self._closed:
            return
        if self.session:
            self.session.close()
        await super().close()

    async def connect(self):
        await self.accept()
    
    async def disconnect(self, code):
        try:
            if self.is_auth:
                await sync_to_async(OperaLogging.session)(self.user,self.ip,self.resource,"close",self.log)
            else:
                await sync_to_async(OperaLogging.session)(self.user,self.ip,self.resource,"faild")
        except Exception:
            pass
        return await super().disconnect(code)
    
    async def receive(self,text_data):
        try:
            data = json.loads(text_data)
            message = data.get('message',None)
        except Exception:
            await self.send("传参错误,请重试")
            return

        if not self.is_auth:
            await self.auth(data)
            return
        await self.session.send(message)


    async def create_session(self,resource,voucher):
        hostname = resource.ipv4_address if resource.ipv4_address else resource.ipv6_address
        username = voucher.username
        password = voucher.password
        port = getattr(resource, 'port', 22)
        self.session = AsyncSSHClient()
        self.session.set_recv_callback(self.send)
        await self.session.connect(
            hostname=hostname,
            username=username,
            password=password,
            port=port,
            timeout=10,
            delay=0.5
        )
        await self.session.set_on_disconnect(self.close)
    async def auth(self,data):
        """
        auth 的 Docstring
        :param data: {
            "token":str,
            "resource_id:int,
            "voucher_id":int,
            "message":Object
        }
        """
        try:
            token = data.get("token")
            resource_id = data.get("resource_id")
            voucher_id = data.get("voucher_id")
            if not all([token, resource_id, voucher_id]):
                raise ValueError("参数错误")
            user_id = await self._verify_token(token)
            self.user,has_perm,self.resource,voucher = await self._check_permissions(user_id, resource_id, voucher_id)
            if has_perm:
                self.is_auth = True
                self.ip = get_ws_client_ip(self.scope)
                try:
                    await self.create_session(self.resource,voucher)
                except Exception as e:
                    await self.send(text_data=json.dumps({"code":400,"status": "fail", "msg": "连接超时"}))
                    await self.close()
                    return
                self.log = await sync_to_async(OperaLogging.session)(self.user,self.ip,self.resource,"active")
                #await self.send(text_data=json.dumps({"code":200,"status": "success", "msg": "认证成功"}))
            else:
                await self.send(text_data=json.dumps({"code":403,"error": "无权限"}))
                await self.close()

        except Exception as e:
            await self.send(text_data=json.dumps({"code":403,"error": "认证失败"}))
            await self.close()
    
    @database_sync_to_async
    def _verify_token(self, token_str):
        """同步方法：验证 JWT 并返回 user_id"""
        try:
            access = AccessToken(token_str)  # ← simplejwt 是同步的，必须放这里
            return access.payload["user_id"]
        except Exception:
            raise ValueError("token错误")

    @database_sync_to_async
    def _check_permissions(self, user_id, resource_id, voucher_id):
        """同步方法：执行所有 ORM 查询和权限判断"""
        try:
            user = User.objects.get(id=user_id)
            resource = Resource.objects.get(id=resource_id)
            voucher = ResourceVoucher.objects.get(id=voucher_id)
            roles = user.roles.all()
            # 资源权限
            resource_perm = (
                BaseAuth.objects.filter(role__in=roles, permission__code='resource.self.read').exists() or
                ResourceAuth.objects.filter(role__in=roles, permission__code='resource.self.read', resource=resource).exists() or
                ResourceAuth.objects.filter(user=user, permission__code='resource.self.read', resource=resource).exists()
            )
            # 凭证权限
            voucher_perm = (
                BaseAuth.objects.filter(role__in=roles, permission__code='resource.voucher.read').exists() or
                ResourceVoucherAuth.objects.filter(role__in=roles, permission__code='resource.voucher.read', voucher=voucher).exists() or
                ResourceVoucherAuth.objects.filter(user=user, permission__code='resource.voucher.read', voucher=voucher).exists()
            )
            return user,resource_perm and voucher_perm,resource,voucher

        except Exception:
            return None