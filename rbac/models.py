from django.db import models


def avatar_upload_path(instance, filename):
    return f'avatars/user_{instance.id}/{filename}'

# Create your models here.
class User(models.Model):
    class Meta:
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

    group = models.ManyToManyField('UserGroup',related_name='users')
    roles = models.ManyToManyField('Role',through='UserRole',related_name='users')

    @property
    def is_authenticated(self):
        return True

class Role(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=20, unique=True)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(null=True, blank=True)
    status = models.BooleanField(default=True)
    protected = models.BooleanField(default=False)
    create_date = models.DateTimeField(auto_now_add=True)
    update_date = models.DateTimeField(auto_now=True)

    create_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='create_roles')
    update_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='update_roles')

class UserRole(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey('rbac.User', on_delete=models.CASCADE)
    role = models.ForeignKey('rbac.Role', on_delete=models.CASCADE)
    create_date = models.DateTimeField(auto_now_add=True)

class Permission(models.Model):
    #生产固定表
    id = models.AutoField(primary_key=True)
    scope = models.CharField(max_length=10)
    object = models.CharField(max_length=10)
    action = models.CharField(max_length=10)
    code = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=20)


class UserGroup(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=20, unique=True)
    code = models.CharField(max_length=20, unique=True)
    status = models.BooleanField(default=True)
    remark = models.TextField(null=True, blank=True)
    create_date = models.DateTimeField(auto_now_add=True)
    update_date = models.DateTimeField(auto_now=True)

    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='children')
    create_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='create_groups')
    update_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='update_groups')