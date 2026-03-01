import asyncio
import asyncssh

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



def my_recv_backcall(data):
    print(data,end='',flush=True)


if __name__ == '__main__':
    def my_recv_callback(data):
        print("Received:", repr(data))

    async def main():
        client = AsyncSSHClient()
        client.set_recv_callback(my_recv_callback)

        await client.connect('example.com', 'user', 'password')

        await client.send('ls -l\n')
        await asyncio.sleep(2)  # 等待输出

        await client.close()

    # 运行
    asyncio.run(main())