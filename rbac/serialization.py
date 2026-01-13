import re

from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from .models import User,Role,Permission
from Utils.public import verify_password, encrypt_password

from Utils.modelViewSet import ERRMSG

read_only = {'read_only':True}
write_only = {'write_only':True}

class LoginSerializer(serializers.Serializer):
    account = serializers.CharField(max_length=20, required=True,error_messages={
        'required':ERRMSG.REQUIRED.ACCOUNT,
        'max_length':ERRMSG.MAX.ACCOUNT + '20字符'
    })
    password = serializers.CharField(max_length=20, required=True,error_messages={
        'required':ERRMSG.REQUIRED.PASSWORD,
        'max_length':ERRMSG.MAX.PASSWORD + '20字符'
    })

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(max_length=20, required=True,error_messages={
        'required':ERRMSG.REQUIRED.OLD_PASSWORD,
        'max_length':ERRMSG.MAX.PASSWORD + '20字符'
    })
    new_password = serializers.CharField(max_length=20, required=True,error_messages={
        'required': ERRMSG.REQUIRED.PASSWORD,
        'max_length':ERRMSG.MAX.PASSWORD + '20字符'
    })

    def validate(self,attrs):
        user = self.context['user']
        old = attrs.get('old_password')
        if not verify_password(old,user.password):
            raise serializers.ValidationError({'old_password':ERRMSG.ERROR.PASSWORD})
        new = attrs.get('new_password')
        if verify_password(new,user.password):
            raise serializers.ValidationError({'new_password':ERRMSG.ERROR.NEW_OLD_EQ})
        return attrs

    def save(self, **kwargs):
        user = self.context['user']
        user.password = encrypt_password(self.validated_data['new_password'])
        user.save()
        return user

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = "__all__"
        extra_kwargs = {
            'id':read_only,
            'account': {
                **write_only,
                'error_messages': {
                    'required': ERRMSG.REQUIRED.ACCOUNT,
                },
                'validators': [
                    UniqueValidator(
                        queryset=User.objects.all(),
                        message=ERRMSG.UNIQUE.ACCOUNT
                    )
                ],
            },
            'password':{
                **write_only,
                'error_messages':{
                    'required': ERRMSG.REQUIRED.PASSWORD,
                }
            },
            'email':{
                'validators': [
                    UniqueValidator(
                        queryset=User.objects.all(),
                        message=ERRMSG.UNIQUE.EMAIL
                    )
                ],
                'error_messages': {
                    'unique': ERRMSG.UNIQUE.EMAIL,
                    'invalid': ERRMSG.INVALID.EMAIL,
                },
            },
            'protected':read_only,
            'phone_number': {
                'error_messages':{
                    'unique':ERRMSG.UNIQUE.PHONE,
                },
            },
            'update_date':read_only,
            'login_date':read_only,
            'group':read_only,
            'roles':read_only,
        }
    def validate(self,attrs):
        if attrs.get('password'):
            attrs['password'] = encrypt_password(attrs['password'])
        return attrs

class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = "__all__"
        exclude = ['perms']
        extra_kwargs = {
            'id':read_only,
            'name':{
                "validators": [
                    UniqueValidator(
                        queryset=Role.objects.all(),
                        message=ERRMSG.UNIQUE.NAME
                    )
                ],
                "error_messages": {
                    "required": ERRMSG.REQUIRED.NAME,
                }
            },
            'code': {
                "validators": [
                    UniqueValidator(
                        queryset=Role.objects.all(),
                        message=ERRMSG.UNIQUE.CODE
                    )
                ],
                "error_messages": {
                    "required": ERRMSG.REQUIRED.CODE,
                }
            },
            "protected":read_only,
            "create_date":read_only,
            "update_date":read_only,
        }
class RolePermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ['id','perms']
        extra_kwargs = {
            'id':read_only,
        }
class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = '__all__'