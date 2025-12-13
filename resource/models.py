from django.db import models

# Create your models here.
class Resource(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=20, unique=True)
    code = models.CharField(max_length=20, unique=True)
    status = models.BooleanField(default=True)
    ipv4_address = models.GenericIPAddressField(protocol='IPv4', unique=True)
    ipv6_address = models.GenericIPAddressField(protocol='IPv6', unique=True, null=True, blank=True)
    domain = models.CharField(max_length=100, unique=True, null=True, blank=True)
    port = models.IntegerField(default=22)
    
    is_production = models.BooleanField(default=False)
    description = models.TextField(null=True, blank=True)
    create_date = models.DateTimeField(auto_now_add=True)
    update_date = models.DateTimeField(auto_now=True)
    group = models.ForeignKey('ResourceGroup', on_delete=models.SET_NULL, null=True, blank=True, related_name='resources')
    resource_type = models.ForeignKey('ResourceType', on_delete=models.SET_NULL, null=True, blank=True, related_name='resources')
    protocol = models.ForeignKey('Protocol', on_delete=models.SET_NULL, null=True, blank=True, related_name='resources')

class ResourceAccount(models.Model):
    id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=50)
    password = models.CharField(max_length=256)
    private_key = models.TextField(null=True, blank=True)
    is_default = models.BooleanField(default=False)
    description = models.TextField(null=True, blank=True)
    create_date = models.DateTimeField(auto_now_add=True)
    update_date = models.DateTimeField(auto_now=True)

    resource = models.ForeignKey(Resource, on_delete=models.CASCADE, related_name='accounts')
    create_user = models.ForeignKey('rbac.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='create_resource_accounts')

class ResourceGroup(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=20, unique=True)
    description = models.TextField(null=True, blank=True)
    create_date = models.DateTimeField(auto_now_add=True)
    update_date = models.DateTimeField(auto_now=True)

    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='children')
    

class Protocol(models.Model):
    #生产固定表
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=20, unique=True)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(null=True, blank=True)
    status = models.BooleanField(default=True)

class ResourceType(models.Model):
    #生产固定表
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=20, unique=True)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(null=True, blank=True)
    status = models.BooleanField(default=True)
