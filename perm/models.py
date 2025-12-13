from django.db import models

# Create your models here.

class BaseAuth(models.Model):
    id = models.AutoField(primary_key=True)
    role = models.ForeignKey('rbac.Role', on_delete=models.CASCADE,related_name='base_authorizations')
    permission = models.ForeignKey('rbac.Permission', on_delete=models.CASCADE, related_name='base_authorizations')
    create_date = models.DateTimeField(auto_now_add=True)

class ResourceAuth(models.Model):
    id = models.AutoField(primary_key=True)
    role = models.ForeignKey('rbac.Role', on_delete=models.CASCADE, related_name='resource_authorizations')
    permission = models.ForeignKey('rbac.Permission', on_delete=models.CASCADE, related_name='resource_authorizations')
    resource = models.ForeignKey('resource.Resource', on_delete=models.CASCADE, related_name='resource_authorizations')
    create_date = models.DateTimeField(auto_now_add=True)

class ResourceAccountAuth(models.Model):
    id = models.AutoField(primary_key=True)
    role = models.ForeignKey('rbac.Role', on_delete=models.CASCADE, related_name='account_authorizations')
    permission = models.ForeignKey('rbac.Permission', on_delete=models.CASCADE, related_name='account_authorizations')
    account = models.ForeignKey('resource.ResourceAccount', on_delete=models.CASCADE, related_name='account_authorizations')
    create_date = models.DateTimeField(auto_now_add=True)