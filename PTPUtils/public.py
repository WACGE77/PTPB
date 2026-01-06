from django.core.paginator import Paginator
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

def get_page(request,query):
    page_size = request.data.get('page_size',10)
    page_number = request.data.get('page_number',1)
    try:
        page_number = int(page_number)
        page_size = int(page_size)
    except Exception:
        page_size = 10
        page_number = 1
    page_size = min(page_size,100)
    paginator = Paginator(query, page_size)
    total = paginator.count
    page = paginator.page(page_number).object_list
    return page,total