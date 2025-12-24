import ipaddress
def get_ws_client_ip(scope):
    """
    从 Django Channels 的 WebSocket scope 中获取客户端真实 IP。
    
    特性：
    - 优先读取 X-Forwarded-For（支持多层代理）
    - 自动跳过内网 IP（10.x, 172.16-31.x, 192.168.x, 127.0.0.1 等）
    - fallback 到直连 IP（scope['client'][0]）
    - 支持 IPv4 和 IPv6
    - 防御无效 IP 字符串
    
    返回:
        str: 客户端公网 IP 地址，若无法获取则返回 '0.0.0.0'
    """
    # 1. 尝试从 headers 中提取 X-Forwarded-For
    headers = dict(scope.get('headers', []))
    xff_header = headers.get(b'x-forwarded-for')
    
    if xff_header:
        try:
            # 解码并分割 IP 列表（X-Forwarded-For: client, proxy1, proxy2）
            ip_list = [ip.strip() for ip in xff_header.decode('latin1').split(',')]
            for ip_str in ip_list:
                if not ip_str:
                    continue
                try:
                    ip_obj = ipaddress.ip_address(ip_str)
                    # 跳过私有、回环、保留地址，返回第一个公网 IP
                    if not (ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_reserved):
                        return str(ip_obj)
                except ValueError:
                    continue  # 忽略非法 IP
            # 如果全是内网 IP，返回第一个（保持连接可追踪）
            if ip_list:
                return ip_list[0]
        except (UnicodeDecodeError, AttributeError):
            pass  # header 格式异常，跳过

    # 2. 尝试从 X-Real-IP 获取（Nginx 常用）
    real_ip_header = headers.get(b'x-real-ip')
    if real_ip_header:
        try:
            ip_str = real_ip_header.decode('latin1').strip()
            ip_obj = ipaddress.ip_address(ip_str)
            if not (ip_obj.is_private or ip_obj.is_loopback):
                return str(ip_obj)
        except (ValueError, UnicodeDecodeError):
            pass

    # 3. fallback：直接连接的客户端 IP
    client_info = scope.get('client')
    if client_info and isinstance(client_info, (list, tuple)) and len(client_info) > 0:
        remote_ip = client_info[0]
        if remote_ip:
            # 可选：这里也可以过滤内网，但通常直连就是真实 IP
            return remote_ip

    return '0.0.0.0'