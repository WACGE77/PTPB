import re

from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from Utils.Const import READ_ONLY_FILED, WRITE_ONLY_FILED, KEY
from .models import User,Role,Permission
from Utils.before import verify_password, encrypt_password

from Utils.modelViewSet import ERRMSG



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
            'id':READ_ONLY_FILED,
            'account': {
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
                **WRITE_ONLY_FILED,
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
            'protected':READ_ONLY_FILED,
            'phone_number': {
                'error_messages':{
                    'unique':ERRMSG.UNIQUE.PHONE,
                },
            },
            'update_date':READ_ONLY_FILED,
            'login_date':READ_ONLY_FILED,
            'group':READ_ONLY_FILED,
            'roles':READ_ONLY_FILED,
        }
    def validate(self,attrs):
        if attrs.get('password'):
            attrs['password'] = encrypt_password(attrs['password'])
        return attrs
    def update(self,instance, validated_data):
        self.validated_data.pop('account',None)
        updated_instance = super().update(instance, validated_data)
        return updated_instance

class UserRoleSerializer(serializers.ModelSerializer):
    roles = serializers.PrimaryKeyRelatedField(many=True,write_only=True,queryset=Role.objects.all())
    class Meta:
        model = User
        fields = ['id','roles']
        read_only_fields = ['id']
        extra_kwargs = {
            'roles': {
                'error_messages':{
                    'does_not_exist':ERRMSG.ABSENT.ROLE
                }
            }
        }



class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        exclude = ['perms']

class RolePermissionSerializer(serializers.ModelSerializer):
    perms = serializers.PrimaryKeyRelatedField(
        queryset=Permission.objects.all(),
        many=True,
        required=False  # 如果允许为空，否则设为 True
    )
    class Meta:
        model = Role
        fields = ['id','perms']
        read_only_fields = ['id']
    def validate(self,attrs):
        perms = attrs.get('perms')
        if not perms or any(16 <= perm.id <= 23 for perm in perms):
            raise serializers.ValidationError({KEY.PERMISSIONS:ERRMSG.ERROR.PERMISSION})
        return attrs
    def save(self):
        if self.instance:
            perms = self.validated_data['perms']
            self.instance.perms.set(perms)
class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = '__all__'

