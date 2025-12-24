from django.db import models

# Create your models here.

class BaseAuth(models.Model):
    id = models.AutoField(primary_key=True)
    role = models.ForeignKey('rbac.Role', on_delete=models.CASCADE,related_name='base_authorizations')
    permission = models.ForeignKey('rbac.Permission', on_delete=models.CASCADE, related_name='base_authorizations')
    create_date = models.DateTimeField(auto_now_add=True)

class BaseResourceAuth(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey('rbac.User',null=True,blank=True,on_delete=models.CASCADE,related_name='%(class)ss')
    role = models.ForeignKey('rbac.Role',null=True,blank=True,on_delete=models.CASCADE, related_name='%(class)ss')
    permission = models.ForeignKey('rbac.Permission', on_delete=models.CASCADE, related_name='%(class)ss')
    protected = models.BooleanField(default=False)
    create_date = models.DateTimeField(auto_now_add=True)
    class Meta:
        abstract = True
        constraints = [
            models.CheckConstraint(
                condition = (
                    models.Q(role__isnull = False,user__isnull=True) |
                    models.Q(role__isnull = True,user__isnull=False)
                ),
                name='%(class)s_exactly_one_of_role_or_user'
            )
        ]

class ResourceAuth(BaseResourceAuth):
    resource = models.ForeignKey(
        'resource.Resource', 
        on_delete=models.CASCADE, 
        null=True,
        blank=True,
        related_name='resource_authorizations'
    )

class ResourceVoucherAuth(BaseResourceAuth):
    account = models.ForeignKey(
        'resource.ResourceVoucher', 
        on_delete=models.CASCADE, 
        null=True,
        blank=True,
        related_name='account_authorizations'
    )