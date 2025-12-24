from .models import LoginLog,OperationLog,SessionLog
class OperaLogging:
    @staticmethod
    def login(ip,user,status:str):
        LoginLog.objects.create(ip=ip,user=user,status=status)

    @staticmethod
    def operation(request,operation:str,status:bool=True):
        ip = request.auth.get('ip', '')
        user = request.user
        OperationLog.objects.create(ip=ip,user=user,operation=operation,status=status)

    @staticmethod
    def session(user,ip,resource,status,sessionLog=None):
        if sessionLog:
            sessionLog.status = status
            return sessionLog.save()
        return SessionLog(
            user = user,
            ip = ip,
            resource = resource,
            status=status
        ).save()

        
