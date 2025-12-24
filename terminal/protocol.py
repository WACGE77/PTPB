import socket
import asyncio
import asyncssh
import paramiko
import time
import threading
class SyncSSHClient:
    
    def __init__(self):
        self._client = paramiko.SSHClient()
        self._client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self._hostname = None
        self._username = None
        self._password = None
        self._connect_status = None
        self._recv_backcall = None
        self._recv_thread = None
        self._tty = None
        self._recv_buffer_size = 1024
    
    def connect(self, hostname, username, password,port=22, timeout=10,delay=1):
        if self._recv_backcall is None:
            raise Exception("recv_backcall is None, please set recv_backcall first")
        self._hostname = hostname
        self._username = username
        self._password = password
        self._client.connect(hostname, port, username, password, timeout=timeout)
        self._tty = self._client.invoke_shell()
        time.sleep(delay)
        welcome = self._tty.recv(self._recv_buffer_size).decode()
        self._recv_backcall(welcome)
        self._connect_status = self._tty.active
        self._recv_thread = threading.Thread(target=self._recv_thread_func)
        self._recv_thread.start()


    def _recv_thread_func(self):
        while self._connect_status:
            if self._tty.recv_ready():
                data = self._tty.recv(self._recv_buffer_size).decode()
                self._recv_backcall(data)


    def get_status(self):
        return self._connect_status

    def send(self, data):
        try:
            self._tty.send(data)
        except socket.error as e:
            self._connect_status = False

    def set_recv_callback(self, backcall):
        self._recv_backcall = backcall

    def close(self):
        self._connect_status = False
        self._tty.close()
        self._client.close()
        self._recv_thread.join()
        self._recv_backcall = None
        self._recv_thread = None
        self._tty = None
        self._client = None

class AsyncSSHClient:
    def __init__(self):
        self._conn = None
        self._process = None
        self._recv_callback = None
        self._task = None
        self._connected = False

    async def connect(self, hostname, username, password, port=22, timeout=10, delay=1):
        if self._recv_callback is None:
            raise ValueError("recv_callback is not set. Please call set_recv_callback() first.")

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

            # 等待初始欢迎信息（可选）
            await asyncio.sleep(delay)
            if self._process.stdout.at_eof():
                welcome = ""
            else:
                welcome = await self._process.stdout.read(1024)
            await self._recv_callback(welcome)

            # 启动接收任务
            self._task = asyncio.create_task(self._recv_loop())

        except Exception as e:
            self._connected = False
            raise e
    
    async def _recv_loop(self):
        try:
            while self._connected and not self._process.stdout.at_eof():
                data = await self._process.stdout.read(1024)
                if data:
                    await self._recv_callback(data)
        except Exception:
            pass
        finally:
            self._connected = False

    def set_recv_callback(self, callback):
        """设置接收数据的回调函数（必须是普通函数或可调用对象）"""
        self._recv_callback = callback

    async def send(self, data: str):
        if not self._connected or self._process.stdin.is_closing():
            raise ConnectionError("SSH connection is not active.")
        self._process.stdin.write(data)

    def get_status(self) -> bool:
        return self._connected

    async def resize(self, cols: int, rows: int):
        if not self._process or not self._connected:
            return

        try:
            await self._process.channel.change_terminal_size(
                cols=cols,
                rows=rows
            )
        except Exception as e:
            print("resize failed:", e)

    async def close(self):
        self._connected = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
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
        self._task = None
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