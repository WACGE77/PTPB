from .models import LoginLog
class Logging:
    @staticmethod
    def login(ip,user,status:str):
        LoginLog.objects.create(ip=ip,user=user,status=status)