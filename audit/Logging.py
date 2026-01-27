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
        ip = request.auth.get('ip', '')
        user = request.user
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
    