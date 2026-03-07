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
    color_depth = serializers.CharField(default='16')
    enable_clipboard = serializers.CharField(default='true')
    
    def validate_color_depth(self, value):
        """验证颜色深度"""
        try:
            return int(value)
        except ValueError:
            raise serializers.ValidationError('请填写合法的整数值。')
    
    def validate_enable_clipboard(self, value):
        """验证剪贴板设置"""
        if value.lower() in ('true', '1', 'yes', 'y'):
            return True
        elif value.lower() in ('false', '0', 'no', 'n'):
            return False
        raise serializers.ValidationError('必须是有效的布尔值。')