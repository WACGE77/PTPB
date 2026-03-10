import asyncio
import asyncssh
import logging
import socket
from Utils.Const import CONFIG

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


class AsyncRDPClient(BaseProtocolClient):
    """RDP协议客户端"""
    
    def __init__(self):
        super().__init__()
        self._conn = None
        # 从配置文件读取 RDP 配置
        try:
            rdp_config = CONFIG.get('RDP', {})
            self._host = rdp_config.get('HOST', '106.13.85.137')
            self._port = rdp_config.get('PORT', 8888)
        except Exception as e:
            logger.error(f"读取配置错误: {e}")
            # 使用默认值
            self._host = "106.13.85.137"
            self._port = 8888

    def _encode(self, *args):
        """
        编码消息
        """
        return ",".join(f"{len(str(a))}.{a}" for a in args) + ";"

    def _parse_instruction(self, data):
        """
        解析指令
        """
        parts = data.strip(";").split(",")
        if not parts:
            return None, []
        cmd_part = parts[0].split(".", 1)
        if len(cmd_part) != 2:
            return None, []
        cmd = cmd_part[1]
        
        args = []
        for p in parts[1:]:
            if "." in p:
                _, v = p.split(".", 1)
                args.append(v)
        
        return cmd, args

    async def connect(self, host, username, password, port=3389, timeout=30, resolution="1024x768", color_depth=16, enable_clipboard=True):
        """
        建立 RDP 连接，通过socket
        
        Args:
            host: 主机地址
            username: 用户名
            password: 密码
            port: 端口号，默认为 3389
            timeout: 连接超时时间（秒），默认为 30
            resolution: 分辨率，默认为 1024x768
            color_depth: 颜色深度，默认为 16
            enable_clipboard: 是否启用剪贴板，默认为 True
        """
        if self._recv_callback is None:
            raise ValueError("recv_callback is not set. Please call set_recv_callback() first.")
        if self._connected:
            raise ValueError("RDP connection is already active.")

        try:
            # 连接到服务器
            logger.info(f"尝试连接到 Guacamole 服务器: {self._host}:{self._port}")
            self._conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._conn.settimeout(timeout)
            self._conn.connect((self._host, self._port))
            logger.info("成功连接到 Guacamole 服务器")
            self._connected = True

            # 1. 发送 select 指令
            select_message = self._encode("select", "rdp")
            logger.debug(f"发送 select 指令: {select_message}")
            self._conn.sendall(select_message.encode())

            # 2. 接收 args 指令
            data = b""
            while b";" not in data:
                chunk = self._conn.recv(4096)
                if not chunk:
                    raise ConnectionError("服务器连接意外关闭")
                data += chunk
            
            instr = data.decode()
            logger.debug(f"收到 args 指令: {instr[:100]}...")

            # 3. 发送 size 指令
            width, height = resolution.split("x")
            size_message = self._encode("size", width, height)
            logger.debug(f"发送 size 指令: {size_message}")
            self._conn.sendall(size_message.encode())

            # 4. 发送 connect 指令
            # 解析 args 指令，获取参数列表
            cmd, args = self._parse_instruction(instr)
            if cmd != "args":
                raise ConnectionError("意外的指令，期望 args")
            
            # 构建 connect 指令参数
            connect_args = []
            for arg in args:
                if arg == "VERSION_1_3_0":
                    connect_args.append("VERSION_1_3_0")
                elif arg == "hostname":
                    connect_args.append(host)
                elif arg == "port":
                    connect_args.append(str(port))
                elif arg == "domain":
                    connect_args.append("")  # 为空
                elif arg == "username":
                    connect_args.append(username)
                elif arg == "password":
                    connect_args.append(password)
                elif arg == "width":
                    connect_args.append(width)
                elif arg == "height":
                    connect_args.append(height)
                elif arg == "dpi":
                    connect_args.append("96")  # 默认 DPI
                else:
                    connect_args.append("")  # 其他参数为空
            
            connect_message = self._encode("connect", *connect_args)
            logger.debug("发送 connect 指令")
            self._conn.sendall(connect_message.encode())

            # 启动接收循环
            self._recv_task = asyncio.create_task(self._recv_loop())

        except Exception as e:
            self._connected = False
            if self._conn:
                try:
                    self._conn.close()
                except Exception:
                    pass
            logger.error(f"RDP 连接错误: {e}")
            raise ConnectionError(f"无法连接到 RDP 服务器: {e}")

    async def _recv_loop(self):
        logger.debug("开始 RDP 接收循环...")
        logger.debug(f"连接状态: {self._connected}")
        logger.debug(f"接收回调: {self._recv_callback}")
        
        try:
            while self._connected:
                try:
                    data = b""
                    while b";" not in data:
                        chunk = self._conn.recv(4096)
                        if not chunk:
                            logger.info("服务器连接关闭")
                            break
                        data += chunk
                    
                    if not data:
                        break
                    
                    instr = data.decode()
                    logger.debug(f"收到指令: {instr}")
                    
                    # 解析指令
                    cmd, args = self._parse_instruction(instr)
                    
                    # 处理指令
                    if cmd == "ready":
                        logger.info("RDP 连接准备就绪")
                        if self._recv_callback:
                            try:
                                # 使用 text_data 参数发送消息
                                await self._recv_callback(text_data="RDP connection established successfully")
                                logger.debug("成功发送 RDP 连接就绪响应")
                            except Exception as e:
                                logger.error(f"发送 RDP 连接就绪响应失败: {e}")
                    elif cmd == "png" or cmd == "jpg":
                        logger.debug("收到绘图指令")
                        if self._recv_callback:
                            await self._recv_callback(instr)
                    elif cmd == "cursor":
                        logger.debug("收到光标指令")
                        if self._recv_callback:
                            await self._recv_callback(instr)
                    elif cmd == "sync":
                        logger.debug("收到同步指令")
                        if self._recv_callback:
                            await self._recv_callback(instr)
                    elif cmd == "error":
                        logger.error(f"收到错误指令: {args}")
                        if self._recv_callback:
                            await self._recv_callback(f"RDP 错误: {args}")
                    else:
                        logger.debug(f"收到未知指令: {cmd}")
                        if self._recv_callback:
                            await self._recv_callback(instr)
                except socket.timeout:
                    logger.debug("Socket 超时，继续等待...")
                    continue
                except ConnectionResetError:
                    logger.info("连接被重置")
                    break
        except Exception as e:
            logger.error(f"接收循环错误: {e}")
        finally:
            logger.debug("接收循环结束，关闭连接...")
            await self.close()

    async def send(self, data: str):
        if not self._connected:
            raise ConnectionError("RDP connection is not active.")
        
        if self._conn:
            # RDP 协议不支持 stdin，使用 key 事件
            logger.debug(f"发送键盘事件: {data}")
            # 这里可以实现键盘事件的发送
            # 例如：对于每个字符，发送 key 指令
        else:
            # 模拟RDP连接
            logger.debug(f"[模拟RDP] 发送数据: {data}")
            if self._recv_callback:
                await self._recv_callback(f"[模拟RDP] 已接收: {data}")

    async def resize(self, cols: int, rows: int):
        """
        调整 RDP 会话窗口大小
        
        Args:
            cols: 列数
            rows: 行数
        """
        if not self._connected:
            return
        
        if self._conn:
            # 发送 size 指令
            size_message = self._encode("size", cols, rows)
            logger.debug(f"发送 size 指令: {size_message}")
            self._conn.sendall(size_message.encode())
        else:
            # 模拟RDP连接
            logger.debug(f"[模拟RDP] 调整窗口大小: {cols}x{rows}")
            if self._recv_callback:
                await self._recv_callback(f"[模拟RDP] 窗口大小已调整为: {cols}x{rows}")

    async def close(self):
        await super().close()
        if self._conn:
            try:
                self._conn.close()
            except Exception:
                pass
        # 清理引用
        self._conn = None