from django.utils import timezone

from Utils.before import get_client_ip
from .models import LoginLog,OperationLog,SessionLog
class OperaLogging:
    @staticmethod
    def login(request,status:str):
        ip = get_client_ip(request)
        LoginLog.objects.create(ip=ip,user=request.user,status=status)

    @staticmethod
    def operation(request,operation:str,status:bool=True):
        ip = ''
        if hasattr(request, 'auth') and request.auth is not None:
            ip = request.auth.get('ip', '') if hasattr(request.auth, 'get') else ''
        # 为了避免IP为空的错误，添加一个默认值
        if not ip:
            ip = '127.0.0.1'
        user = request.user if hasattr(request, 'user') else None
        if user:
            OperationLog.objects.create(ip=ip,user=user,operation=operation,status=status)
    # 异步有问题用不了
    @staticmethod
    def session(user,ip,resource,voucher,status,sessionLog=None):
        if sessionLog:
            sessionLog.status = status
            sessionLog.end_time = timezone.now()
            sessionLog.save()
            return sessionLog
        sessionLog = SessionLog(
            user = user,
            ip = ip,
            resource = resource,
            voucher = voucher,
            status=status
        )
        sessionLog.save()
        return sessionLog
    