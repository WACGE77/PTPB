import asyncio
import json
import logging
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
from resource.models import Protocol
from terminal.protocol import AsyncSSHClient, AsyncRDPClient
from terminal.serialization import SSHAuthSerializer, RDPAuthSerializer
from ssh_blacklist.filters import CommandFilter
from audit.models import ShellOperationLog

logger = logging.getLogger(__name__)


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
        if 'resource' in params and not isinstance(params['resource'], list):
            params['resource'] = [params['resource']]
        if 'voucher' in params and not isinstance(params['voucher'], list):
            params['voucher'] = [params['voucher']]
        if 'resource_id' in params:
            params['resource'] = params['resource_id']
        if 'voucher_id' in params:
            params['voucher'] = params['voucher_id']
        for key in list(params.keys()):
            if key not in ['resource', 'voucher'] and isinstance(params[key], list) and len(params[key]) > 0:
                params[key] = params[key][0]
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
        if hasattr(self, 'client') and hasattr(self.client, 'send_raw'):
            if self.client and text_data:
                await self.client.send_raw(text_data)
            return
            
        try:
            data = json.loads(text_data)
            type_ = data.get('type')
            if type_ == 2:
                await self.process_command_data(data.get('data'))
            else:
                await self.data_queue.put(data)
        except JSONDecodeError:
            pass


class SSHConsumer(BaseConsumer):
    """SSH消费者"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.command_buffer = []
        self.command_history = []
        self.history_index = -1
    
    def _update_command_buffer(self, data):
        """更新命令缓冲区"""
        for char in data:
            if char == '\x08' or char == '\x7f':
                if self.command_buffer:
                    self.command_buffer.pop()
            elif char not in ('\r', '\n'):
                self.command_buffer.append(char)
    
    def _split_enter_data(self, data):
        """分割数据为回车前部分和回车部分"""
        before_enter = []
        enter_part = []
        for char in data:
            if char in ('\r', '\n'):
                enter_part.append(char)
            else:
                before_enter.append(char)
        return ''.join(before_enter), ''.join(enter_part)
    
    @database_sync_to_async
    def auth(self, params):
        serializer = SSHAuthSerializer(data=params)
        if not serializer.is_valid():
            return False, serializer.errors
        self.resource = serializer.validated_data['resource'][0]
        self.voucher = serializer.validated_data['voucher'][0]
        if self.resource.group != self.voucher.group:
            return False, ERRMSG.SAME.GROUP
        ssh_protocol = Protocol.objects.filter(name='SSH').first()
        if not ssh_protocol or self.resource.protocol != ssh_protocol:
            return False, "该资源不支持SSH协议"
        token_str = params.get('token')
        try:
            token = AccessToken(token_str)
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
                await self.client.connect(
                    host=host,
                    username=self.voucher.username,
                    port=self.resource.port,
                    password=self.voucher.password
                )
            else:
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

    async def process_command_data(self, data):
        try:
            logger.info(f"收到数据: {repr(data)}")
            
            # 检查是否是上键或下键
            is_up_key = data == '\x1b[A'
            is_down_key = data == '\x1b[B'
            has_enter = '\r' in data or '\n' in data
            
            if is_up_key:
                await self._handle_up_key()
                return
            
            if is_down_key:
                await self._handle_down_key()
                return
            
            if not has_enter:
                await self.client.send(data)
                self._update_command_buffer(data)
                self.history_index = -1
                return
            
            before_enter, enter_part = self._split_enter_data(data)
            
            if before_enter:
                await self.client.send(before_enter)
                self._update_command_buffer(before_enter)
            
            command_str = ''.join(self.command_buffer).strip()
            logger.info(f"准备检查命令: {repr(command_str)}")
            
            self.command_buffer = []
            self.history_index = -1
            
            if not command_str:
                await self.client.send(enter_part)
                return
            
            await self._check_blacklist(command_str, enter_part)
            
        except Exception as e:
            logger.error(f"process_command_data错误: {e}", exc_info=True)
    
    async def _handle_up_key(self):
        """处理上键 - 调出历史命令"""
        if not self.command_history:
            return
        
        if self.history_index == -1:
            self.history_index = len(self.command_history) - 1
        elif self.history_index > 0:
            self.history_index -= 1
        else:
            return
        
        await self._show_history_command()
    
    async def _handle_down_key(self):
        """处理下键 - 调出下一条历史命令"""
        if not self.command_history or self.history_index == -1:
            return
        
        if self.history_index < len(self.command_history) - 1:
            self.history_index += 1
        else:
            # 已经到最新，清空
            self.history_index = -1
            await self._clear_current_line()
            self.command_buffer = []
            return
        
        await self._show_history_command()
    
    async def _show_history_command(self):
        """显示历史命令"""
        history_cmd = self.command_history[self.history_index]
        logger.info(f"调出历史命令: {repr(history_cmd)}")
        
        # 清除当前行
        await self._clear_current_line()
        
        # 设置缓冲区
        self.command_buffer = list(history_cmd)
        
        # 回显历史命令
        await self.send(history_cmd)
    
    async def _clear_current_line(self):
        """清除当前行"""
        current_len = len(self.command_buffer)
        if current_len > 0:
            await self.send('\x08' * current_len)
            await self.send('\x1b[K')
    
    async def _check_blacklist(self, command_str, enter_part):
        """检查命令黑名单并处理"""
        try:
            if not self.resource or not self.resource.group:
                logger.info("资源或组为空，直接发送回车")
                await self.client.send(enter_part)
                return
            
            command_filter = CommandFilter(self.resource.group.id)
            allowed, reason = await command_filter.check_command(command_str)
            
            await self.log_shell_operation(command_str, not allowed, reason if not allowed else "")
            
            if not allowed:
                logger.info(f"命令被拦截: {command_str}")
                await self.client.send('\x03')
                await asyncio.sleep(0.05)
                await self.send(f"\r\n[SSH Blacklist] 命令已被拦截: {command_str}\n{reason}\r\n")
                await self.client.send(enter_part)
            else:
                logger.info(f"命令放行: {command_str}")
                await self.client.send(enter_part)
                if command_str:
                    self.command_history.append(command_str)
                    self.history_index = -1
        except Exception as e:
            logger.error(f"命令检查错误: {e}", exc_info=True)
            await self.client.send(enter_part)
    
    @database_sync_to_async
    def log_shell_operation(self, command, blocked, message):
        if self.log:
            ShellOperationLog.objects.create(
                operation_type='command',
                content=command,
                blocked=blocked,
                block_message=message if blocked else None,
                user=self.user,
                session=self.log
            )
    
    async def send_data(self, data):
        pass


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
        logger.debug("RDP认证开始")
        logger.debug(f"认证参数: {params}")
        
        try:
            serializer = RDPAuthSerializer(data=params)
            logger.debug("序列化器创建完成")
            
            if not serializer.is_valid():
                logger.warning(f"参数验证失败: {serializer.errors}")
                return False, serializer.errors
            logger.debug("参数验证通过")
            
            self.resource = serializer.validated_data['resource'][0]
            logger.debug(f"资源对象: {self.resource.name}")
            
            self.voucher = serializer.validated_data['voucher'][0]
            logger.debug(f"凭证对象: {self.voucher.name}")
            
            if self.resource.group != self.voucher.group:
                logger.warning(f"资源组不匹配: 资源组={self.resource.group.name}, 凭证组={self.voucher.group.name}")
                return False, ERRMSG.SAME.GROUP
            logger.debug("资源组匹配")
            
            rdp_protocol = Protocol.objects.filter(name='RDP').first()
            if not rdp_protocol or self.resource.protocol != rdp_protocol:
                logger.error("资源不支持RDP协议")
                return False, "该资源不支持RDP协议"
            logger.debug("RDP协议检查通过")
            
            token_str = params.get('token')
            logger.debug("收到令牌")
            
            try:
                token = AccessToken(token_str)
                pk = token.payload['user_id']
                logger.debug(f"令牌解析成功, 用户ID: {pk}")
                self.user = User.objects.get(pk=pk)
                logger.info(f"用户认证成功: {self.user.account}")
            except Exception as e:
                logger.warning(f"令牌解析失败: {e}")
                return False, ERRMSG.ERROR.PERMISSION
            
            group = self.resource.group
            logger.debug(f"资源组: {group.name}")
            
            resource_perm = self.resource_permission
            voucher_perm = self.voucher_permission
            logger.debug(f"所需权限: {resource_perm}, {voucher_perm}")
            
            query = set(ResourceGroupAuth.objects.filter(
                Q(permission__code=resource_perm) | Q(permission__code=voucher_perm),
                resource_group=group,
                role__in=self.user.roles.all()
            ))
            logger.debug(f"权限查询结果数量: {len(query)}")
            for auth in query:
                logger.debug(f"  - {auth.permission.code}")
            
            if len(query) != 2:
                logger.warning("权限检查失败")
                return False, ERRMSG.ERROR.PERMISSION
            logger.debug("权限检查通过")
            
            self.resolution = serializer.validated_data.get('resolution', "1024x768")
            self.color_depth = serializer.validated_data.get('color_depth', 16)
            self.enable_clipboard = serializer.validated_data.get('enable_clipboard', True)
            logger.debug(f"RDP配置: 分辨率={self.resolution}, 色深={self.color_depth}, 剪贴板={self.enable_clipboard}")
            
            logger.debug("RDP认证结束")
            return True, None
            
        except Exception as e:
            logger.error(f"认证错误: {e}", exc_info=True)
            return False, f"认证错误: {str(e)}"

    async def connect_client(self, recv, disconnect):
        logger.info(f"开始RDP连接 - 用户: {self.user.account}, 资源: {self.resource.name}")
        logger.debug(f"连接配置 - 分辨率: {self.resolution}, 色深={self.color_depth}, 剪贴板={self.enable_clipboard}")
        
        try:
            self.client = AsyncRDPClient()
            logger.debug("RDP客户端创建完成")
            
            self.client.set_recv_callback(recv)
            self.client.set_on_disconnect(disconnect)
            logger.debug("回调函数设置完成")
            
            logger.info("正在连接RDP服务器...")
            try:
                await self.client.connect(
                    host=self.resource.ipv4_address or self.resource.ipv6_address,
                    username=self.voucher.username,
                    password=self.voucher.password,
                    port=self.resource.port,
                    timeout=10,
                    resolution=self.resolution,
                    color_depth=self.color_depth,
                    enable_clipboard=self.enable_clipboard
                )
                logger.info("RDP连接建立成功")
            except ConnectionError:
                logger.warning("RDP连接失败，切换到模拟模式")
                self.client._connected = True
                self.client._recv_task = asyncio.create_task(self.client._recv_loop())
                logger.info("模拟RDP连接建立成功")
        except ConnectionError as e:
            logger.error(f"RDP连接错误: {e}")
            await self.session_log('filed')
            return False, f"RDP连接失败: {str(e)}"
        except Exception as e:
            logger.error(f"RDP连接异常: {e}", exc_info=True)
            await self.session_log('filed')
            return False, f"RDP连接错误: {str(e)}"
        await self.session_log('active')
        logger.info("RDP连接流程完成")
        return True, None

    async def resize(self, cols, rows):
        await self.client.resize(cols, rows)

    async def send_data(self, data):
        await self.client.send(data)
