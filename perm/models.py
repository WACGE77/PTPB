from django.db import models

# Create your models here.

class BaseAuth(models.Model):
    class Meta:
        db_table = 'system_auth'
    id = models.AutoField(primary_key=True)
    role = models.ForeignKey('rbac.Role', on_delete=models.CASCADE,related_name='base_authorizations')
    permission = models.ForeignKey('rbac.Permission', on_delete=models.CASCADE, related_name='base_authorizations')
    create_date = models.DateTimeField(auto_now_add=True)

class ResourceGroupAuth(models.Model):
    class Meta:
        db_table = 'resource_group_auth'
    id = models.AutoField(primary_key=True)
    role = models.ForeignKey('rbac.Role', on_delete=models.CASCADE, related_name='resource_group_authorizations')
    permission = models.ForeignKey('rbac.Permission', on_delete=models.CASCADE, related_name='resource_group_authorizations')
    resource_group = models.ForeignKey('resource.ResourceGroup', on_delete=models.CASCADE, related_name='resource_group_authorizations')
    protected = models.BooleanField(default=False)
    create_date = models.DateTimeField(auto_now_add=True)
