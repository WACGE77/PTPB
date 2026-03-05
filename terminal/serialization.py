from rest_framework import serializers

from Utils.Const import ERRMSG
from resource.models import Resource, Voucher


class BaseAuthSerializer(serializers.Serializer):
    """认证序列化器基类，包含通用逻辑"""
    
    resource = serializers.PrimaryKeyRelatedField(
        queryset=Resource.objects.all(),
        error_messages={
            'does_not_exist': ERRMSG.ABSENT.RESOURCE
        },
        many=True,
    )
    voucher = serializers.PrimaryKeyRelatedField(
        queryset=Voucher.objects.all(),
        error_messages={
            'does_not_exist': ERRMSG.ABSENT.VOUCHER
        },
        many=True,
    )
    token = serializers.CharField(read_only=True)


class SSHAuthSerializer(BaseAuthSerializer):
    """SSH认证序列化器"""
    pass


class RDPAuthSerializer(BaseAuthSerializer):
    """RDP认证序列化器"""
    
    resolution = serializers.CharField(default='1024x768')
    color_depth = serializers.IntegerField(default=16)
    enable_clipboard = serializers.BooleanField(default=True)