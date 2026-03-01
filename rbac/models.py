from django.db import models


def avatar_upload_path(instance, filename):
    return f'avatars/user_{instance.id}/{filename}'

# Create your models here.
class User(models.Model):
    class Meta:
        db_table = 'user'
        verbose_name = '用户'
    id = models.AutoField(primary_key=True)
    account = models.CharField(max_length=20, unique=True,verbose_name='账户')
    password = models.CharField(max_length=256, verbose_name='密码')
    name = models.CharField(max_length=50,blank=True, verbose_name='昵称')
    email = models.EmailField(max_length=100, unique=True,blank=True, verbose_name='邮箱')
    status = models.BooleanField(default=True, verbose_name='是否是正常用户')
    protected = models.BooleanField(default=False, verbose_name='保护标志位')
    phone_number = models.CharField(max_length=11, unique=True,null=True,blank=True, verbose_name='电话')
    avatar = models.ImageField(upload_to=avatar_upload_path,default='avatars/default.png', null=True, blank=True, verbose_name='头像')
    create_date = models.DateTimeField(auto_now_add=True)
    update_date = models.DateTimeField(auto_now=True)
    login_date = models.DateTimeField(null=True, blank=True)
    remark = models.TextField(null=True, blank=True)

    roles = models.ManyToManyField('Role',through='UserRole',related_name='users')

    @property
    def is_authenticated(self):
        return True

class Role(models.Model):
    class Meta:
        db_table = 'role'
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=20, unique=True)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(null=True, blank=True)
    status = models.BooleanField(default=True)
    protected = models.BooleanField(default=False)
    create_date = models.DateTimeField(auto_now_add=True)
    update_date = models.DateTimeField(auto_now=True)
    perms = models.ManyToManyField('rbac.Permission',through='perm.BaseAuth',related_name='roles')

class UserRole(models.Model):
    class Meta:
        db_table = 'user_role'
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey('rbac.User', on_delete=models.CASCADE)
    role = models.ForeignKey('rbac.Role', on_delete=models.CASCADE)
    create_date = models.DateTimeField(auto_now_add=True)

class Permission(models.Model):
    class Meta:
        db_table = 'permission'
    #生产固定表
    id = models.AutoField(primary_key=True)
    scope = models.CharField(max_length=15)
    object = models.CharField(max_length=15)
    action = models.CharField(max_length=10)
    code = models.CharField(max_length=40, unique=True)
    name = models.CharField(max_length=20)

class Route(models.Model):
    class Meta:
        db_table = 'route'
    id = models.AutoField(primary_key=True)
    path = models.CharField(max_length=255, unique=True)
    component = models.CharField(max_length=255)
    title = models.CharField(max_length=100)
    icon = models.CharField(max_length=100)
    permission_code = models.CharField(max_length=100, null=True, blank=True)
    parent_id = models.IntegerField(null=True, blank=True)
    order = models.IntegerField(default=0)
    status = models.BooleanField(default=True)
    create_date = models.DateTimeField(auto_now_add=True)
    update_date = models.DateTimeField(auto_now=True)
