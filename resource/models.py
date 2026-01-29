from django.db import models
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from rest_framework.exceptions import ValidationError

from Utils.Const import ERRMSG, CONFIG

# Create your models here.
class Resource(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=20, unique=True)
    status = models.BooleanField(default=True)
    ipv4_address = models.GenericIPAddressField(protocol='IPv4', unique=True, null=True, blank=True)
    ipv6_address = models.GenericIPAddressField(protocol='IPv6', unique=True, null=True, blank=True)
    domain = models.CharField(max_length=100, unique=True, null=True, blank=True)
    port = models.IntegerField(default=22)
    description = models.TextField(null=True, blank=True)
    create_date = models.DateTimeField(auto_now_add=True)
    update_date = models.DateTimeField(auto_now=True)
    vouchers = models.ManyToManyField('resource.Voucher', related_name='resources', blank=True)
    group = models.ForeignKey('ResourceGroup', on_delete=models.SET_DEFAULT,default=1, related_name='resources')
    protocol = models.ForeignKey('Protocol', on_delete=models.CASCADE, related_name='resources')
    class Meta:
        db_table = 'resource'
        constraints = [
            models.CheckConstraint(
                condition = (
                    models.Q(ipv4_address__isnull = False,ipv6_address__isnull=True) |
                    models.Q(ipv6_address__isnull = False,ipv4_address__isnull=True)
                ),
                name='resource_exactly_one_ip'
            )
        ]

class Voucher(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(unique=True,max_length=20)
    username = models.CharField(max_length=20)
    password = models.CharField(max_length=256,null=True,blank=True)
    private_key = models.TextField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    create_date = models.DateTimeField(auto_now_add=True)
    update_date = models.DateTimeField(auto_now=True)
    group = models.ForeignKey('ResourceGroup', on_delete=models.SET_DEFAULT,default=1, related_name='ssh_vouchers')
    class Meta:
        db_table = 'voucher'
        constraints = [
            models.CheckConstraint(
                condition = (
                    models.Q(password__isnull = False,private_key__isnull=True) |
                    models.Q(private_key__isnull = False,password__isnull=True)
                ),
                name='%(class)s_exactly_one_of_password_or_private_key'
            )
        ]


class ResourceGroup(models.Model):
    class Meta:
        db_table = 'resource_group'
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=20, unique=True)
    description = models.TextField(null=True, blank=True)
    protected = models.BooleanField(default=False)
    create_date = models.DateTimeField(auto_now_add=True)
    update_date = models.DateTimeField(auto_now=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    level = models.SmallIntegerField(default=0,blank=True,null=True)
    root = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='leaf')

class Protocol(models.Model):
    #生产固定表
    class Meta:
        db_table = 'protocol'
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=20, unique=True)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(null=True, blank=True)


@receiver(pre_save, sender=ResourceGroup)
def pre_group(sender,instance,**kwargs):
    if instance.parent and instance.parent.level >= CONFIG.GROUP_LEVEL_MAX:
        raise ValidationError(ERRMSG.CONFIG.GROUP_LEVEL_MAX)

@receiver(post_save, sender=ResourceGroup)
def post_group(sender, instance,created, **kwargs):
    if created:
        update_data = {}
        if instance.parent:
            update_data['root'] = instance.parent.root
            update_data['level'] = instance.parent.level + 1
        else:
            update_data['root'] = instance
            update_data['level'] = 0
        print(update_data)
        if update_data:
            try:
                post_save.disconnect(post_group,sender=ResourceGroup)
                ResourceGroup.objects.filter(pk=instance.pk).update(**update_data)
            finally:
                post_save.connect(post_group,sender=ResourceGroup)

