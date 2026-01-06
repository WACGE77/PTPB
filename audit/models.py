from django.db import models



# Create your models here.
class LoginLog(models.Model):
    id = models.AutoField(primary_key=True)
    ip = models.GenericIPAddressField()
    user = models.ForeignKey('rbac.User', on_delete=models.CASCADE)
    status = models.CharField(max_length=10,)
    date = models.DateTimeField(auto_now_add=True)

class OperationLog(models.Model):
    id = models.AutoField(primary_key=True)
    ip = models.GenericIPAddressField()
    user = models.ForeignKey('rbac.User', on_delete=models.CASCADE)
    operation = models.CharField(max_length=50)
    status = models.BooleanField()
    date = models.DateTimeField(auto_now_add=True)

class SessionLog(models.Model):
    id = models.AutoField(primary_key=True)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20)  # e.g., 'active', 'closed', 'failed' 0,1,2
    user = models.ForeignKey('rbac.User', on_delete=models.CASCADE)
    ip = models.GenericIPAddressField()
    resource = models.ForeignKey('resource.Resource', on_delete=models.CASCADE, related_name='session_records')
    voucher = models.ForeignKey('resource.ResourceVoucher', on_delete=models.CASCADE, related_name='session_records')
    
class ShellOperationLog(models.Model):
    id = models.AutoField(primary_key=True)
    operation_type = models.CharField(max_length=20)
    content = models.CharField(max_length=100)
    operation_time = models.DateTimeField(auto_now_add=True)  # in seconds
    user = models.ForeignKey('rbac.User', on_delete=models.CASCADE)
    session = models.ForeignKey(SessionLog, on_delete=models.CASCADE, related_name='operation_logs')