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

    async def connect(self, hostname, username, password, port=22, timeout=10, delay=1):
        async with self._lock:
            if self._recv_callback is None:
                raise ValueError("recv_callback is not set. Please call set_recv_callback() first.")
            if self._connected:
                raise ValueError("SSH connection is already active.")

            try:
                self._conn = await asyncio.wait_for(
                    asyncssh.connect(
                        hostname,
                        port=port,
                        username=username,
                        password=password,
                        known_hosts=None  # 相当于 AutoAddPolicy
                    ),
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
                if data:
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

            if self._on_disconnect:
                self._on_disconnect()

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