import fnmatch
import asyncio
import json
import logging
import re
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
from terminal.protocol import AsyncSSHClient, AsyncRDPClient, AsyncMySQLClient
from terminal.serialization import SSHAuthSerializer, RDPAuthSerializer
from ssh_blacklist.models import DangerCommandRule
from audit.models import ShellOperationLog

logger = logging.getLogger(__name__)

ANSI_ESCAPE_RE = re.compile(r'\x1b\[[0-9;]*[a-zA-Z]|\x1b\][^\x07]*\x07')


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
        try:
            data = json.loads(text_data)
            type_ = data.get('type')
            if type_ == 2:
                await self.process_command_data(data.get('data'))
            else:
                await self.data_queue.put(data)
        except JSONDecodeError:
            pass
        except Exception as e:
            logger.error(f"receive处理错误: {e}", exc_info=True)


class SSHConsumer(BaseConsumer):
    """
    SSH消费者 - 纯透传模式 + 后置审计机制

    功能特性：
    - 纯透传：所有按键直接发送给SSH，不拦截任何输入（方向键/Tab/历史命令正常）
    - 回显监控：从SSH回显流中提取用户执行的命令
    - 后置审计：检测危险命令并记录日志
    - 实时告警：命中黑名单规则时向前端推送告警消息

    状态机设计：
    - echo_buffer: 行缓冲区，用于拼接不完整的数据包
    - command_candidate: 候选命令文本（等待确认）
    - last_line_was_prompt: 上一行是否为提示符（状态标志）

    处理流程：
    1. hooked_recv 接收SSH回显数据
    2. _process_echo 解析回显，识别提示符和命令
    3. _audit_command 执行异步审计（规则匹配+日志记录+告警推送）
    """

    INVALID_COMMAND_MARKERS = ['^C', '^D', '^Z', '\x03', '\x04', '\x1a']

    PROMPT_PATTERNS = [
        # 标准格式: user@host:~#
        r'[\w.-]+@[\w.-]+[#:~][^#$]*?[#$]\s*(.+)$',
        # 方括号格式: [root@server ~]$ (更通用的匹配)
        r'\[[^\]]+\]\s*[#$>\$]\s*(.+)$',
        # 简单提示符: #
        r'^(?:\s*[#$>]\s*)(.+)$',
        # PowerShell: PS >
        r'PS\s+[^\s>]+\s*>\s*(.+)$',
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.echo_buffer = ""
        self.command_candidate = None
        self.last_line_was_prompt = False

    @staticmethod
    def _strip_ansi(text):
        """
        移除ANSI转义序列（颜色、光标控制等）
        
        Args:
            text: 可能包含ANSI转义序列的文本
            
        Returns:
            清理后的纯文本
        """
        return ANSI_ESCAPE_RE.sub('', text) if text else ''

    @staticmethod
    def _is_prompt_line(line):
        """
        判断一行文本是否为命令提示符
        
        支持的格式：
        - root@host:~# (标准bash/zsh)
        - user@host:~$ (普通用户)
        - bash-5.1# (简化版)
        - [root@host ~]# (方括号格式)
        - mysql> (数据库提示符)
        - PS C:\\> (PowerShell)
        
        Args:
            line: 待检测的文本行
            
        Returns:
            bool: 是否为提示符行
        """
        if not line:
            return False
        stripped = line.rstrip()
        return (stripped.endswith('$') or stripped.endswith('#') or
                stripped.endswith('$ ') or stripped.endswith('# ') or
                stripped.endswith('>') or stripped.endswith('> '))

    @staticmethod
    def _looks_like_command(text):
        """
        快速判断文本是否像有效的shell命令
        
        用于过滤掉Ctrl+C、空行、纯符号等无效输入，
        防止产生垃圾审计记录。
        
        Args:
            text: 待检查的文本
            
        Returns:
            bool: 是否像有效命令
        """
        if not text or len(text.strip()) < 1:
            return False
        for marker in SSHConsumer.INVALID_COMMAND_MARKERS:
            if marker in text:
                return False
        return True

    @staticmethod
    def _match_rule(cmd, rule):
        """
        匹配黑名单规则
        
        支持三种匹配模式：
        - exact: 精确匹配 (cmd == pattern)
        - prefix: 前缀匹配 (cmd.startswith(pattern))
        - regex: 正则匹配 (re.search(pattern, cmd))
        
        Args:
            cmd: 用户执行的命令
            rule: DangerCommandRule 规则对象
            
        Returns:
            bool: 是否命中规则
        """
        import re
        
        pattern = rule.pattern.strip()
        if not pattern:
            return False

        # 清洗命令：去除可能的控制字符、多余空格
        cmd_clean = re.sub(r'[\x00-\x1f\x7f]', '', cmd)
        cmd_clean = re.sub(r'\s+', ' ', cmd_clean).strip()
        
        # 如果清洗后为空，直接返回 False
        if not cmd_clean:
            return False

        rule_type = rule.type
        
        # 提取命令的第一个单词，用于匹配
        cmd_first_word = cmd_clean.split()[0] if cmd_clean.split() else cmd_clean

        if rule_type == 'exact':
            # 精确匹配：匹配完整命令或匹配第一个单词
            return cmd_clean == pattern or cmd_first_word == pattern
        elif rule_type == 'prefix':
            actual = pattern[:-1] if pattern.endswith('*') else pattern
            # 前缀匹配：匹配完整命令前缀或匹配第一个单词前缀
            return cmd_clean.startswith(actual) or cmd_first_word.startswith(actual)
        elif rule_type == 'regex':
            try:
                return bool(re.search(pattern, cmd_clean))
            except re.error:
                logger.warning(f"规则正则表达式无效: {pattern}")
                return False
        else:
            return False

    @staticmethod
    def _extract_prompt_command(line):
        """
        从回显行中提取用户命令（纯命令，不含prompt前缀）

        策略：找到所有 prompt 匹配，选择最短的捕获组并清洗作为纯命令

        Args:
            line: 包含prompt和命令的完整行

        Returns:
            str|None: 提取出的纯命令
        """
        import re

        best_cmd = None
        all_matches = []
        for i, pattern in enumerate(SSHConsumer.PROMPT_PATTERNS):
            matches = list(re.finditer(pattern, line))
            if matches:
                print(f"[ECHO-DEBUG] Pattern {i+1} matched! Matches: {len(matches)}")
            for match in matches:
                cmd = match.group(1).strip()
                if cmd:
                    # 清洗命令：去除可能的控制字符、多余空格
                    clean_cmd = re.sub(r'[\x00-\x1f\x7f]', '', cmd)
                    clean_cmd = re.sub(r'\s+', ' ', clean_cmd).strip()
                    print(f"[ECHO-DEBUG] Pattern {i+1} captured: {repr(cmd)} -> {repr(clean_cmd)}")
                    all_matches.append(clean_cmd)
                    if best_cmd is None or len(clean_cmd) < len(best_cmd):
                        best_cmd = clean_cmd

        if all_matches:
            print(f"[ECHO-DEBUG] All matches: {[repr(c) for c in all_matches]}")
        if best_cmd:
            print(f"[ECHO-DEBUG] Final extracted cmd: {repr(best_cmd)} (len={len(best_cmd)})")
        return best_cmd if best_cmd else None

    async def _process_echo(self, data):
        """
        处理SSH回显流，使用状态机提取用户命令并触发审计

        状态机三种状态：
        1. is_prompt=True: 当前行是纯提示符 → 审计之前的候选命令
        2. has_embedded_cmd=True and last_prompt=True: 当前行是 prompt+command → 直接提取并审计
        3. 其他情况: 普通输出或候选命令设置

        Args:
            data: 从SSH接收到的原始数据（可能包含ANSI序列）
        """
        print(f"[ECHO-DEBUG] _process_echo called with data length: {len(data) if data else 0}")
        clean = self._strip_ansi(data)
        if not clean:
            return

        self.echo_buffer += clean
        while '\n' in self.echo_buffer:
            line, self.echo_buffer = self.echo_buffer.split('\n', 1)
            line = line.strip('\r').strip()

            if not line:
                continue

            is_prompt = self._is_prompt_line(line)
            has_embedded_cmd = self._extract_prompt_command(line) is not None

            print(f"[ECHO-DEBUG] Line: {repr(line[:80])}, is_prompt={is_prompt}, has_cmd={has_embedded_cmd}, last_was_prompt={self.last_line_was_prompt}")

            if is_prompt:
                if self.command_candidate and self._looks_like_command(self.command_candidate):
                    cmd = self.command_candidate.strip()
                    print(f"[ECHO-DEBUG] *** AUDIT TRIGGERED from prompt: {repr(cmd)} ***")
                    logger.info(f"[审计] 检测到命令: {repr(cmd)}")
                    task = asyncio.ensure_future(self._audit_command(cmd))
                    task.add_done_callback(
                        lambda t: t.exception() and logger.error(f"[审计] 任务异常: {t.exception()}")
                    )
                self.command_candidate = None
                self.last_line_was_prompt = True

            elif has_embedded_cmd:
                cmd = self._extract_prompt_command(line)
                if cmd and self._looks_like_command(cmd):
                    print(f"[ECHO-DEBUG] *** AUDIT TRIGGERED from embedded: {repr(cmd)} ***")
                    logger.info(f"[审计] 提取命令: {repr(cmd)}")
                    task = asyncio.ensure_future(self._audit_command(cmd))
                    task.add_done_callback(
                        lambda t: t.exception() and logger.error(f"[审计] 任务异常: {t.exception()}")
                    )
                self.command_candidate = None
                self.last_line_was_prompt = False

            else:
                if self.last_line_was_prompt and self._looks_like_command(line):
                    self.command_candidate = line
                else:
                    self.command_candidate = None
                self.last_line_was_prompt = False

    async def _audit_command(self, cmd):
        """
        后置审计：检查命令是否命中黑名单规则
        
        流程：
        1. 查询该资源组的所有活跃规则
        2. 逐一匹配规则（支持 exact/prefix/regex）
        3. 记录审计日志到数据库（无论是否命中都记录）
        4. 如果命中规则，通过WebSocket推送告警给前端
        
        Args:
            cmd: 用户执行的命令字符串
        """
        if not cmd:
            return

        group_id = self.resource.group.id

        @database_sync_to_async
        def check_rules():
            rules = list(DangerCommandRule.objects.filter(group_id=group_id, is_active=True))
            for rule in rules:
                if self._match_rule(cmd, rule):
                    return True, f'{rule.pattern}'
            return False, ''

        blocked, reason = await check_rules()

        @database_sync_to_async
        def save_log():
            from django.utils import timezone
            ShellOperationLog.objects.create(
                operation_type='command',
                content=cmd,
                blocked=blocked,
                block_message=reason if blocked else '',
                user=self.user,
                session=self.log
            )

        try:
            await save_log()
        except Exception as e:
            logger.error(f"保存审计日志失败: {e}")

        if blocked:
            logger.warning(f"[后置审计] 危险命令: {cmd}, 原因: {reason}")
            try:
                await self.send(text_data=json.dumps({
                    'type': 'danger_alert',
                    'data': {'command': cmd, 'reason': reason}
                }))
            except Exception as e:
                logger.error(f"推送告警消息失败: {e}")

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
        # 重置状态变量（解决重连黑屏问题）
        self.echo_buffer = ""
        self.command_candidate = None
        self.last_line_was_prompt = False
        
        self.client = AsyncSSHClient()

        async def hooked_recv(data):
            await recv(data)
            asyncio.ensure_future(self._process_echo(data))

        self.client.set_recv_callback(hooked_recv)
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
            await self.client.send(data)
        except Exception as e:
            logger.error(f"发送数据到SSH失败: {e}", exc_info=True)

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


class MysqlConsumer(AsyncWebsocketConsumer):
    """MySQL数据库WebSocket消费者"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = None
        self.ip = None
        self.resource = None
        self.voucher = None
        self.mysql_client = None

    async def connect(self):
        """处理WebSocket连接"""
        from rest_framework_simplejwt.tokens import AccessToken
        from rbac.models import User

        params = parse_qs(self.scope['query_string'].decode('utf-8'))
        self.ip = get_ws_client_ip(self.scope)

        try:
            token_str = params.get('token', [None])[0]
            if not token_str:
                await self.close(1008, 'Missing token')
                return

            token = AccessToken(token_str)
            user_id = token.payload['user_id']
            self.user = await User.objects.aget(id=user_id)

            resource_id = params.get('resource_id', [None])[0]
            voucher_id = params.get('voucher_id', [None])[0]

            if not resource_id or not voucher_id:
                await self.close(1008, 'Missing resource_id or voucher_id')
                return

            from resource.models import Resource, Voucher
            self.resource = await Resource.objects.aget(id=resource_id)
            self.voucher = await Voucher.objects.aget(id=voucher_id)

            self.mysql_client = AsyncMySQLClient()
            self.mysql_client.set_recv_callback(self.send_result)

            host = self.resource.ipv4_address
            port = self.resource.port or 3306
            username = self.voucher.username
            password = self.voucher.password

            await self.mysql_client.connect(host, username, password, port)

            await self.accept()
            logger.info(f"MySQL连接成功: {self.user} -> {host}:{port}")
        except Exception as e:
            logger.error(f"MySQL连接失败: {e}", exc_info=True)
            await self.close(1011, str(e))

    async def disconnect(self, close_code):
        """处理断开连接"""
        if self.mysql_client:
            await self.mysql_client.close()
            self.mysql_client = None
        logger.info(f"MySQL连接已断开: {close_code}")

    async def receive(self, text_data=None):
        """接收前端消息"""
        if not text_data:
            return
        if self.mysql_client:
            await self.mysql_client.send(text_data)

    async def send_result(self, result):
        await self.send(text_data=result)

    async def send_error(self, error):
        """发送错误信息到前端"""
        await self.send(text_data=json.dumps({'type': 'error', 'data': {'error': str(error)}}))
