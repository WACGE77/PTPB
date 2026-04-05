import asyncio
import asyncssh
import logging
import json
import uuid
import websockets
from typing import Optional, Tuple
from Utils.Const import CONFIG
from terminal.guacamole import guacamole_service

logger = logging.getLogger(__name__)


class BaseProtocolClient:
    """协议客户端基类，定义通用接口"""
    
    def __init__(self):
        self._connected = False
        self._on_disconnect = None
        self._recv_callback = None
        self._recv_task = None

    def set_on_disconnect(self, callback):
        """设置断开连接的回调函数"""
        self._on_disconnect = callback

    def set_recv_callback(self, callback):
        """设置接收数据的回调函数"""
        self._recv_callback = callback

    async def send(self, data: str):
        """发送数据"""
        raise NotImplementedError("子类必须实现send方法")

    @property
    def get_status(self) -> bool:
        """获取连接状态"""
        return self._connected

    async def resize(self, cols: int, rows: int):
        """调整窗口大小"""
        raise NotImplementedError("子类必须实现resize方法")

    async def close(self):
        """关闭连接"""
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


class AsyncSSHClient(BaseProtocolClient):
    """SSH协议客户端"""
    
    def __init__(self):
        super().__init__()
        self._conn = None
        self._process = None
        self._lock = asyncio.Lock()

    async def connect(self, host, username, port=22, timeout=10, delay=1,
                      password=None, private_key=None, private_key_password=None):
        """
        建立 SSH 连接，支持密码或私钥认证
        
        Args:
            host: 主机地址
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
                    'host': host,
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

    async def send(self, data: str):
        if not self._connected or self._process.stdin.is_closing():
            raise ConnectionError("SSH connection is not active.")
        self._process.stdin.write(data)

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
            await super().close()
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


class GuacamoleInstruction:
    """Guacamole 协议指令编码/解码"""
    
    @staticmethod
    def encode(opcode: str, *args) -> str:
        """
        编码 Guacamole 指令
        
        格式: length.opcode,length.arg1,length.arg2,...;
        """
        parts = [f"{len(opcode)}.{opcode}"]
        for arg in args:
            arg_str = str(arg) if arg is not None else ""
            parts.append(f"{len(arg_str)}.{arg_str}")
        return ",".join(parts) + ";"
    
    @staticmethod
    def decode(data: str) -> Tuple[str, list]:
        """
        解码 Guacamole 指令
        
        Returns:
            (opcode, [args...])
        """
        if not data or not data.endswith(';'):
            return None, []
        
        data = data[:-1]
        parts = data.split(',')
        if not parts:
            return None, []
        
        opcode = None
        args = []
        
        for i, part in enumerate(parts):
            if '.' in part:
                length_str, value = part.split('.', 1)
                try:
                    length = int(length_str)
                    if i == 0:
                        opcode = value
                    else:
                        args.append(value)
                except ValueError:
                    continue
        
        return opcode, args


class AsyncRDPClient(BaseProtocolClient):
    """RDP协议客户端 - 通过 Guacamole WebSocket 实现"""
    
    def __init__(self):
        super().__init__()
        self._ws = None
        self._connection_id = None
        self._token = None
        self._data_source = None
        self._lock = asyncio.Lock()
        self._width = 1024
        self._height = 768
        self._mouse_x = 0
        self._mouse_y = 0
        self._mouse_button_state = 0
        self._sync_key = 0

    async def connect(
        self,
        host: str,
        username: str,
        password: str,
        port: int = 3389,
        timeout: int = 30,
        resolution: str = "1024x768",
        color_depth: int = 32,
        enable_clipboard: bool = True,
        connection_name: str = None,
        **kwargs
    ):
        """
        建立 RDP 连接，通过 Guacamole WebSocket
        
        Args:
            host: 目标主机地址
            username: 登录用户名
            password: 登录密码
            port: RDP 端口号，默认 3389
            timeout: 连接超时时间（秒）
            resolution: 分辨率，格式 "宽x高"
            color_depth: 颜色深度 (16, 24, 32)
            enable_clipboard: 是否启用剪贴板
            connection_name: 连接名称（可选，用于在 Guacamole 中标识）
            **kwargs: 额外参数
        """
        if self._recv_callback is None:
            raise ValueError("recv_callback is not set. Please call set_recv_callback() first.")
        if self._connected:
            raise ValueError("RDP connection is already active.")

        try:
            width, height = resolution.split("x")
            self._width = int(width)
            self._height = int(height)
        except (ValueError, AttributeError):
            self._width = 1024
            self._height = 768

        # 即使提供了 connection_name，也要添加 UUID 确保唯一性
        base_name = connection_name or "temp"
        conn_name = f"{base_name}_{uuid.uuid4().hex[:12]}"
        
        try:
            logger.info(f"正在创建临时 Guacamole 连接: {conn_name}")
            
            self._token, self._data_source, self._connection_id = await guacamole_service.create_connection(
                name=conn_name,
                hostname=host,
                port=port,
                username=username,
                password=password,
                color_depth=color_depth,
                width=self._width,
                height=self._height,
                enable_clipboard=enable_clipboard,
                **kwargs
            )
            
            if not self._connection_id:
                raise ConnectionError("无法创建 Guacamole 连接")
            
            logger.info(f"Guacamole 连接已创建: {self._connection_id}")
            
            ws_url = guacamole_service.get_websocket_url(
                self._token,
                self._data_source,
                self._connection_id
            )
            
            logger.info(f"正在连接 Guacamole WebSocket: {ws_url}")
            
            self._ws = await asyncio.wait_for(
                websockets.connect(
                    ws_url,
                    subprotocols=["guacamole"],
                    ping_interval=None,
                    ping_timeout=None
                ),
                timeout=timeout
            )
            
            self._connected = True
            logger.info("Guacamole WebSocket 连接成功")
            
            self._recv_task = asyncio.create_task(self._recv_loop())
            logger.info(f"接收循环任务已创建: {self._recv_task}")
            
        except asyncio.TimeoutError:
            logger.error("连接 Guacamole 超时")
            self._connected = False
            raise ConnectionError("连接 Guacamole 超时")
        except Exception as e:
            logger.error(f"RDP 连接错误: {e}", exc_info=True)
            self._connected = False
            raise ConnectionError(f"RDP 连接失败: {e}")

    async def _recv_loop(self):
        """接收消息循环 - 直接转发所有消息"""
        try:
            while self._connected and self._ws:
                try:
                    message = await asyncio.wait_for(
                        self._ws.recv(),
                        timeout=60.0
                    )
                    
                    if isinstance(message, bytes):
                        message = message.decode('utf-8', errors='ignore')
                    
                    logger.debug(f"收到 Guacamole 消息: {message[:200]}...")
                    
                    if self._recv_callback:
                        await self._recv_callback(text_data=message)
                        
                except asyncio.TimeoutError:
                    if self._connected:
                        try:
                            await self._ws.send("nop;")
                            logger.debug("发送心跳指令")
                        except Exception as e:
                            logger.warning(f"发送心跳指令失败: {e}")
                    continue
                except websockets.exceptions.ConnectionClosed as e:
                    logger.info(f"WebSocket 连接已关闭: {e}")
                    break
                except Exception as e:
                    logger.error(f"接收消息错误: {e}", exc_info=True)
                    # 继续循环，避免因单个消息错误导致整个会话中断
                    continue
                    
        except asyncio.CancelledError:
            logger.debug("接收循环被取消")
        except Exception as e:
            logger.error(f"接收循环错误: {e}", exc_info=True)
        finally:
            logger.info("接收循环结束，开始清理连接")
            await self.close()

    async def _send_instruction(self, opcode: str, *args):
        """发送 Guacamole 指令"""
        if not self._connected or not self._ws:
            return
        
        instruction = GuacamoleInstruction.encode(opcode, *args)
        try:
            await self._ws.send(instruction)
            logger.debug(f"发送指令: {instruction[:100]}...")
        except Exception as e:
            logger.error(f"发送指令失败: {e}")

    async def _send_nop(self):
        """发送心跳指令"""
        await self._send_instruction("nop")

    async def _send_sync_response(self):
        """发送同步响应"""
        await self._send_instruction("sync", self._sync_key)

    async def send(self, data: str):
        """
        发送数据
        
        Args:
            data: JSON 格式的操作数据
        """
        if not self._connected:
            raise ConnectionError("RDP connection is not active.")
        
        try:
            event = json.loads(data)
            event_type = event.get('type')
            
            if event_type == 'key':
                await self._handle_key_event(event)
            elif event_type == 'mouse':
                await self._handle_mouse_event(event)
            elif event_type == 'size':
                await self._handle_size_event(event)
            elif event_type == 'clipboard':
                await self._handle_clipboard_event(event)
            else:
                logger.warning(f"未知事件类型: {event_type}")
                
        except json.JSONDecodeError:
            logger.warning(f"无效的 JSON 数据: {data}")
        except Exception as e:
            logger.error(f"处理事件错误: {e}")

    async def send_raw(self, data: str):
        """
        直接发送原始 Guacamole 协议消息
        
        Args:
            data: 原始 Guacamole 协议消息（如 "nop;", "sync,123;" 等）
        """
        if not self._connected or not self._ws:
            return
        
        try:
            await self._ws.send(data)
            logger.debug(f"发送原始消息: {data[:100]}...")
        except Exception as e:
            logger.error(f"发送原始消息失败: {e}")

    async def _handle_key_event(self, event: dict):
        """
        处理键盘事件
        
        Args:
            event: {"type": "key", "keysym": int, "pressed": bool}
        """
        keysym = event.get('keysym')
        pressed = event.get('pressed', True)
        
        if keysym is not None:
            await self._send_instruction("key", keysym, 1 if pressed else 0)

    async def _handle_mouse_event(self, event: dict):
        """
        处理鼠标事件
        
        Args:
            event: {"type": "mouse", "x": int, "y": int, "button": int, "pressed": bool}
        """
        x = event.get('x', self._mouse_x)
        y = event.get('y', self._mouse_y)
        button = event.get('button', 0)
        pressed = event.get('pressed')
        
        self._mouse_x = x
        self._mouse_y = y
        
        if pressed is not None:
            if pressed:
                self._mouse_button_state |= button
            else:
                self._mouse_button_state &= ~button
        
        await self._send_instruction("mouse", x, y, self._mouse_button_state)

    async def _handle_size_event(self, event: dict):
        """
        处理窗口大小变化事件
        
        Args:
            event: {"type": "size", "width": int, "height": int}
        """
        width = event.get('width', self._width)
        height = event.get('height', self._height)
        
        self._width = width
        self._height = height
        
        await self._send_instruction("size", width, height)

    async def _handle_clipboard_event(self, event: dict):
        """
        处理剪贴板事件
        
        Args:
            event: {"type": "clipboard", "data": str}
        """
        data = event.get('data', '')
        await self._send_instruction("clipboard", data)

    async def resize(self, cols: int, rows: int):
        """
        调整 RDP 会话窗口大小
        
        Args:
            cols: 列数（宽度）
            rows: 行数（高度）
        """
        if not self._connected:
            return
        
        # 确保分辨率至少为1024x768
        width = max(1024, cols)
        height = max(768, rows)
        
        self._width = width
        self._height = height
        
        logger.info(f"调整RDP分辨率: {width}x{height}")
        await self._send_instruction("size", width, height)

    async def send_key(self, keysym: int, pressed: bool = True):
        """
        发送键盘事件（便捷方法）
        
        Args:
            keysym: X11 keysym 值
            pressed: 是否按下
        """
        await self._send_instruction("key", keysym, 1 if pressed else 0)

    async def send_mouse(self, x: int, y: int, button_mask: int = 0):
        """
        发送鼠标事件（便捷方法）
        
        Args:
            x: X 坐标
            y: Y 坐标
            button_mask: 按钮掩码 (1=左键, 2=中键, 4=右键)
        """
        self._mouse_x = x
        self._mouse_y = y
        self._mouse_button_state = button_mask
        await self._send_instruction("mouse", x, y, button_mask)

    async def send_text(self, text: str):
        """
        发送文本（逐字符发送）
        
        Args:
            text: 要发送的文本
        """
        for char in text:
            keysym = ord(char)
            await self.send_key(keysym, True)
            await asyncio.sleep(0.01)
            await self.send_key(keysym, False)
            await asyncio.sleep(0.01)

    async def close(self):
        """关闭连接并清理 Guacamole 连接配置"""
        async with self._lock:
            await super().close()
            
            if self._ws:
                try:
                    await self._send_instruction("disconnect")
                    await self._ws.close()
                except Exception:
                    pass
            
            # 清理 Guacamole 连接配置
            if self._token and self._data_source and self._connection_id:
                try:
                    logger.info(f"正在清理 Guacamole 连接: {self._connection_id}")
                    await guacamole_service.delete_connection(
                        self._token,
                        self._data_source,
                        self._connection_id
                    )
                except Exception as e:
                    logger.warning(f"清理 Guacamole 连接失败: {e}")
            
            self._ws = None
            self._connection_id = None
            self._token = None
            self._data_source = None
            
            logger.info("RDP 连接已关闭")