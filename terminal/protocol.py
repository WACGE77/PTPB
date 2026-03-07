import asyncio
import asyncssh
import aiohttp
import json


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
        self._session = None
        self._websocket = None
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
            
            print(f"Attempting to connect to Guacamole: {self._guacamole_url}")
            
            # 连接到 Guacamole WebSocket
            self._websocket = await asyncio.wait_for(
                self._session.ws_connect(self._guacamole_url),
                timeout=timeout
            )
            print("Successfully connected to Guacamole WebSocket")
            self._connected = True

            # 启动接收循环
            self._recv_task = asyncio.create_task(self._recv_loop())

        except aiohttp.ClientError as e:
            self._connected = False
            if self._session:
                await self._session.close()
            print(f"Guacamole connection error: {e}")
            raise ConnectionError(f"无法连接到 Guacamole 服务器: {e}")
        except asyncio.TimeoutError:
            self._connected = False
            if self._session:
                await self._session.close()
            print("Guacamole connection timeout")
            raise ConnectionError("连接 Guacamole 服务器超时")
        except Exception as e:
            self._connected = False
            if self._session:
                await self._session.close()
            print(f"Unexpected error: {e}")
            raise

    async def _recv_loop(self):
        print("Starting RDP recv loop...")
        print(f"Connected: {self._connected}")
        print(f"WebSocket: {self._websocket}")
        print(f"Recv callback: {self._recv_callback}")
        
        try:
            # 模拟RDP连接的接收循环
            if not self._websocket:
                print("Running in mock mode (no Guacamole)")
                # 模拟RDP连接，定期发送模拟数据
                while self._connected:
                    print("Mock loop iteration...")
                    # 发送模拟的RDP数据
                    if self._recv_callback:
                        print("Sending mock RDP data...")
                        # 模拟RDP连接成功的消息
                        await self._recv_callback('RDP connection established successfully')
                        # 模拟一些RDP数据
                        await self._recv_callback('RDP: Ready for input')
                    else:
                        print("No recv callback set!")
                    # 暂停一段时间
                    await asyncio.sleep(2)
            else:
                print("Running in real mode (Guacamole)")
                # 真实的Guacamole WebSocket连接
                async for msg in self._websocket:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        await self._recv_callback(msg.data)
                    elif msg.type == aiohttp.WSMsgType.CLOSED:
                        break
                    elif msg.type == aiohttp.WSMsgType.ERROR:
                        break
        except Exception as e:
            print(f"Recv loop error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            print("Recv loop ended, closing connection...")
            asyncio.create_task(self.close())

    async def send(self, data: str):
        if not self._connected:
            raise ConnectionError("RDP connection is not active.")
        
        if self._websocket and not self._websocket.closed:
            # 真实的Guacamole WebSocket连接
            await self._websocket.send_str(data)
        else:
            # 模拟RDP连接，打印发送的数据
            print(f"[模拟RDP] 发送数据: {data}")
            # 模拟发送成功
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
        
        if self._websocket and not self._websocket.closed:
            # 真实的Guacamole WebSocket连接
            # 发送 Guacamole 格式的大小调整命令
            resize_command = json.dumps({
                "type": "size",
                "width": cols,
                "height": rows
            })
            await self._websocket.send_str(resize_command)
        else:
            # 模拟RDP连接，打印调整大小的命令
            print(f"[模拟RDP] 调整窗口大小: {cols}x{rows}")
            # 模拟调整成功
            if self._recv_callback:
                await self._recv_callback(f"[模拟RDP] 窗口大小已调整为: {cols}x{rows}")

    async def close(self):
        await super().close()
        if self._websocket and not self._websocket.closed:
            try:
                await self._websocket.close()
            except Exception:
                pass
        if self._session:
            try:
                await self._session.close()
            except Exception:
                pass
        # 清理引用
        self._session = None
        self._websocket = None
        self._guacamole_url = None