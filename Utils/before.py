import bcrypt
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

def encrypt_password(password: str) -> str:
    """
    使用 bcrypt 对密码进行哈希
    返回值是 base64 编码的字符串（可直接存入数据库）
    """
    if not isinstance(password, str):
        raise ValueError("Password must be a string")

    # 生成 salt 并哈希（默认 rounds=12，可根据需要调整）
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt(rounds=12)  # rounds 越高越安全但越慢（建议 10~14）
    hashed = bcrypt.hashpw(password_bytes, salt)

    # 转为字符串存储（bcrypt 哈希本身是兼容 ASCII 的）
    return hashed.decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    """
    验证明文密码是否与 bcrypt 哈希匹配
    """
    try:
        password_bytes = password.encode('utf-8')
        hashed_bytes = hashed.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except Exception:
        return False

def get_client_ip(request):
    IP = request.META.get('HTTP_X_FORWARDED_FOR')
    if IP:
        ip_list = [i.strip() for i in IP.split(',')]
        for read_ip in ip_list:
            if not read_ip.startswith(('10','172','192','127')):
                return read_ip
        return ip_list[0]
    ip = request.META.get('REMOTE_ADDR')
    return ip


def get_ws_client_ip(scope):
    """
    从 WebSocket scope 中获取真实客户端 IP（兼容代理场景）
    :param scope: WebSocket 的 scope 字典
    :return: 真实客户端 IP 字符串
    """
    # 步骤1：先尝试从代理头提取（优先）
    headers = dict(scope['headers'])
    # 转换头名（Channels 中 headers 的键是 bytes 类型，如 b'x-forwarded-for'）
    x_forwarded_for = headers.get(b'x-forwarded-for', b'').decode('utf-8')
    x_real_ip = headers.get(b'x-real-ip', b'').decode('utf-8')

    # 处理 X-Forwarded-For（格式：客户端IP, 代理IP1, 代理IP2...）
    if x_forwarded_for:
        # 取第一个非空 IP（避免多个代理的情况）
        client_ip = x_forwarded_for.split(',')[0].strip()
        if client_ip:
            return client_ip

    # 处理 X-Real-IP
    if x_real_ip:
        return x_real_ip.strip()

    # 步骤2：无代理时，从 scope['client'] 提取
    return scope['client'][0]


def get_token_response(user, data, code=200) -> Response:
    refresh = RefreshToken.for_user(user)
    access = refresh.access_token
    data['token'] = {
        'access': str(access),
        'refresh': str(refresh)
    }
    response = Response(data, status=code)
    response.set_cookie('refresh', str(refresh), httponly=True, expires=refresh.payload['exp'])
    return response
