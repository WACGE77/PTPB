import re

from rest_framework import serializers
from .models import User,Role,Permission
from .utils import verify_password, encrypt_password, phone_pattern, mail_pattern


class LoginSerializer(serializers.Serializer):
    account = serializers.CharField(max_length=20, required=True,error_messages={
        'required':'账号不能为空',
        'max_length':'账号长度不能超过20'
    })
    password = serializers.CharField(max_length=20, required=True,error_messages={
        'required':'账号不能为空',
        'max_length':'账号长度不能超过20'
    })

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(max_length=20, required=True,error_messages={
        'required':'旧密码不能为空',
        'max_length':'旧密码长度不能超过20'
    })
    new_password = serializers.CharField(max_length=20, required=True,error_messages={
        'required': '密码不能为空',
        'max_length': '密码长度不能超过20'
    })

    def validate(self,attrs):
        user = self.context['user']
        old = attrs.get('old_password')
        if not verify_password(old,user.password):
            raise serializers.ValidationError({'old_password':'旧密码错误'})
        new = attrs.get('new_password')
        if verify_password(new,user.password):
            raise serializers.ValidationError({'new_password':'新旧密码不能相同'})
        return attrs

    def save(self, **kwargs):
        user = self.context['user']
        user.password = encrypt_password(self.validated_data['new_password'])
        user.save()
        return user

class ResetPasswordSerializer(serializers.Serializer):
    password = serializers.CharField(max_length=20, required=True,error_messages={
        'required': '密码不能为空',
        'max_length': '密码长度不能超过20'
    })
    def save(self,**kwargs):
        user = self.context['user']
        user.password = encrypt_password(self.validated_data['password'])
        user.save()

class UserAddSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ['account', 'password', 'email','name']


    def save(self,**kwargs):
        account = self.validated_data.get('account')
        password = encrypt_password(self.validated_data.get('password'))
        email = self.validated_data.get('email')
        name = self.validated_data.get('name',account)
        user = User.objects.create(account=account,password=password,email=email,name=name)
        user.roles.add(2)

class UserModifySerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['email','name','phone_number','remark']
        extra_kwargs = {
            'email': {
                'validators': []
            }
        }
    
    def validate_email(self,value):
        if not re.match(mail_pattern,value):
            raise serializers.ValidationError('非法邮箱格式')
        query = User.objects.filter(email=value)
        if self.instance:
            query = query.exclude(id=self.instance.id)
        if query.exists():
           raise serializers.ValidationError('邮箱已被使用') 
        return value

    def validate_phone_number(self,value):
        if not re.match(phone_pattern,value):
            raise serializers.ValidationError({'phone_number':'非法手机号'})
        return value

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id','account','name','email','status','phone_number','create_date','remark','protected']

class IDListSerializer(serializers.Serializer):
    id_list = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=True,
        error_messages={
            'invalid':'ID列表格式错误'
        }
    )

class RoleIDListSerializer(IDListSerializer):
    def validate_id_list(self,value):
        exist = Role.objects.filter(id__in=value).values_list('id',flat=True)
        missing = set(value) - set(exist)
        if missing:
            raise serializers.ValidationError(f'角色ID不存在: {",".join([str(i) for i in missing])}')
        return value
    
class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ['id','name','code','description','create_date','protected']
    
class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = '__all__'