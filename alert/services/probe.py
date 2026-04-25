import socket
import time
import logging
import struct
import select
import asyncio
from typing import Tuple, Optional

logger = logging.getLogger(__name__)


class ProbeService:
    """探针服务"""
    
    @staticmethod
    def ping_host(host: str, timeout: int = 2) -> Tuple[bool, Optional[float], str]:
        """
        ICMP Ping 探测主机存活
        
        Args:
            host: 主机IP或域名
            timeout: 超时时间（秒）
            
        Returns:
            (是否成功, 延迟ms, 消息)
        """
        try:
            # 使用 socket 实现简单的 ping
            start_time = time.time()
            
            # 创建 ICMP socket
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
            except PermissionError:
                # 如果没有权限使用 raw socket，改用 TCP 连接测试
                return ProbeService._tcp_ping_fallback(host, 80, timeout)
            
            sock.settimeout(timeout)
            
            # 构造 ICMP Echo Request 包
            packet_id = int(time.time() * 1000) & 0xFFFF
            packet = ProbeService._create_icmp_packet(packet_id)
            
            try:
                sock.sendto(packet, (host, 0))
                
                # 等待响应
                ready = select.select([sock], [], [], timeout)
                if ready[0]:
                    data, addr = sock.recvfrom(1024)
                    latency = (time.time() - start_time) * 1000
                    return True, round(latency, 2), f'Ping successful, latency: {latency:.2f}ms'
                else:
                    return False, None, 'Request timeout'
            finally:
                sock.close()
                
        except Exception as e:
            logger.error(f'Ping error for {host}: {e}')
            return False, None, str(e)
    
    @staticmethod
    def _tcp_ping_fallback(host: str, port: int, timeout: int) -> Tuple[bool, Optional[float], str]:
        """TCP 连接作为 ping 的备用方案"""
        try:
            start_time = time.time()
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            
            try:
                sock.connect((host, port))
                latency = (time.time() - start_time) * 1000
                return True, round(latency, 2), f'TCP connect successful, latency: {latency:.2f}ms'
            finally:
                sock.close()
        except Exception as e:
            return False, None, f'TCP connect failed: {str(e)}'
    
    @staticmethod
    def _create_icmp_packet(packet_id: int) -> bytes:
        """创建 ICMP Echo Request 包"""
        # ICMP Echo Request (type 8, code 0)
        icmp_type = 8
        icmp_code = 0
        icmp_checksum = 0
        icmp_id = packet_id
        icmp_seq = 1
        
        # 构造数据部分
        data = b'abcdefghijklmnopqrstuvwxyz'
        
        # 构造 ICMP 头
        header = struct.pack('!BBHHH', icmp_type, icmp_code, icmp_checksum, icmp_id, icmp_seq)
        packet = header + data
        
        # 计算校验和
        icmp_checksum = ProbeService._calculate_checksum(packet)
        header = struct.pack('!BBHHH', icmp_type, icmp_code, icmp_checksum, icmp_id, icmp_seq)
        
        return header + data
    
    @staticmethod
    def _calculate_checksum(data: bytes) -> int:
        """计算校验和"""
        checksum = 0
        count_to = (len(data) // 2) * 2
        count = 0
        
        while count < count_to:
            this_val = data[count + 1] * 256 + data[count]
            checksum += this_val
            checksum &= 0xffffffff
            count += 2
        
        if count_to < len(data):
            checksum += data[len(data) - 1]
            checksum &= 0xffffffff
        
        checksum = (checksum >> 16) + (checksum & 0xffff)
        checksum += (checksum >> 16)
        answer = ~checksum & 0xffff
        answer = answer >> 8 | (answer << 8 & 0xff00)
        
        return answer
    
    @staticmethod
    def tcp_port_check(host: str, port: int, timeout: int = 2) -> Tuple[bool, Optional[float], str]:
        """
        TCP 端口探测
        
        Args:
            host: 主机IP或域名
            port: 端口号
            timeout: 超时时间（秒）
            
        Returns:
            (是否成功, 延迟ms, 消息)
        """
        try:
            start_time = time.time()
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            
            try:
                sock.connect((host, port))
                latency = (time.time() - start_time) * 1000
                return True, round(latency, 2), f'Port {port} open, latency: {latency:.2f}ms'
            except ConnectionRefusedError:
                return False, None, f'Port {port} connection refused'
            except socket.timeout:
                return False, None, f'Port {port} connection timeout'
            finally:
                sock.close()
        except Exception as e:
            logger.error(f'TCP port check error for {host}:{port}: {e}')
            return False, None, str(e)
