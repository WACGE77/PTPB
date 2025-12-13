from django.db import models



# Create your models here.
class LoginLog(models.Model):
    id = models.AutoField(primary_key=True)
    ip = models.GenericIPAddressField()
    user = models.ForeignKey('rbac.User', on_delete=models.CASCADE)
    status = models.CharField(max_length=10,)
    date = models.DateTimeField(auto_now_add=True)


class SessionLog(models.Model):
    id = models.AutoField(primary_key=True)
    session_id = models.CharField(max_length=64, unique=True)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20)  # e.g., 'active', 'closed', 'failed'

    login_record = models.ForeignKey(LoginLog, on_delete=models.CASCADE)
    resource = models.ForeignKey('resource.ResourceAccount', on_delete=models.CASCADE, related_name='session_records')
    
class OperationLog(models.Model):
    id = models.AutoField(primary_key=True)
    operation_type = models.CharField(max_length=20)
    content = models.CharField(max_length=100)
    operation_time = models.DateTimeField(auto_now_add=True)  # in seconds
    
    session = models.ForeignKey(SessionLog, on_delete=models.CASCADE, related_name='operation_logs')