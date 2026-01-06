import bcrypt
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from twisted.words.protocols.jabber.xmlstream import hashPassword
from audit.Logging import OperaLogging

phone_pattern = r"^1[3-9]\d{9}$"
mail_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
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

#登录和刷新token用
def get_token_response(user,data,code = 200) -> Response:
    refresh = RefreshToken.for_user(user)
    access = refresh.access_token
    data['token'] = {
        'access': str(access),
        'refresh': str(refresh)
    }
    response = Response(data, status=code)
    response.set_cookie('refresh', str(refresh), httponly=True, expires=refresh.payload['exp'])
    return response

#更新密码用
def reset_password_response(serializer,request) -> Response:
    userobj = serializer.context.get('user', "")
    account = getattr(userobj, 'account', "")
    opera = f'重置{account}密码'
    if serializer.is_valid():
        serializer.save()
        OperaLogging.operation(request, opera, True)
        return Response({'code': 200, 'msg': 'success'}, status=200)
    OperaLogging.operation(request, opera, False)
    return Response({'code': 400, 'msg': 'failure', 'error_msg': serializer.errors}, status=200)

