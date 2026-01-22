from Utils.Const import RESPONSE__200__SUCCESS,RESPONSE__400__FAILED,KEY
from rest_framework.response import Response
from audit.Logging import OperaLogging

def validate_exclusive_params(*args):
    """
    验证多个参数中**有且仅有一个**是非空有效值。
    
    有效值定义：不是 None，且去除首尾空白后不为空字符串。
    
    :param args: 要检查的参数（通常为字符串）
    :raises ValueError: 如果有效参数数量 ≠ 1
    :return: 包含唯一有效值的列表（长度为1）
    """
    valid_values = []
    for item in args:
        if item is not None and isinstance(item, str) and item.strip() != "":
            valid_values.append(item)
        # 如果是非字符串类型（如 int），可根据需要扩展，但凭证场景通常是 str
    
    if len(valid_values) != 1:
        raise ValueError("必须有且仅有一个参数为非空有效值")
    
    return valid_values

phone_pattern = r"^1[3-9]\d{9}$"
mail_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

# 登录和刷新token用


# 更新密码用
def reset_password_response(serializer, request):
    user_obj = serializer.context.get('user', "")
    account = getattr(user_obj, 'account', "")
    opera = f'重置{account}密码'
    if serializer.is_valid():
        serializer.save()
        OperaLogging.operation(request, opera, True)
        return Response(RESPONSE__200__SUCCESS, status=200)
    OperaLogging.operation(request, opera, False)
    return Response({**RESPONSE__400__FAILED, KEY.ERROR: serializer.errors}, status=400)

