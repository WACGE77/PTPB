from rest_framework import serializers

from perm.models import BaseAuth, ResourceAuth

from .models import Resource,ResourceVoucher
from PTPUtils.public import validate_exclusive_params
class ResourceSerializer(serializers.ModelSerializer):
    # vouchers = serializers.PrimaryKeyRelatedField(
    #     queryset=ResourceVoucher.objects.all(),
    #     many=True,
    #     required=False,      # 👈 关键：设为非必填
    #     allow_empty=True     # 👈 允许空列表 []
    # )
    class Meta:
        model = Resource
        fields = "__all__"
        read_only_fields = ['id']
    def validate(self, attrs):
        ipv4 = attrs.get('ipv4_address',getattr(self.instance,'ipv4_address',None))
        ipv6 = attrs.get('ipv6_address',getattr(self.instance,'ipv6_address',None))
        try:
            validate_exclusive_params(ipv4,ipv6)
        except ValueError:
            raise serializers.ValidationError({"error":'ipv4或ipv6必须有一个不为空,且只有一个'})
        return attrs
class ResourceVoucherSerializer(serializers.ModelSerializer):
    resource_id = serializers.IntegerField(required=False)
    class Meta:
        model = ResourceVoucher
        fields = "__all__"
        read_only_fields = ['id']
    def validate(self, attrs):
        password = attrs.get('password',getattr(self.instance,'password',None))
        private_key = attrs.get('private_key',getattr(self.instance,'private_key',None))
        try:
            validate_exclusive_params(password,private_key)
        except ValueError:
            raise serializers.ValidationError({"error":'password或private_key必须有一个不为空,且只有一个'})
        return attrs
    def create(self, validated_data):
        # 移除 resource_id，防止传给模型
        validated_data.pop('resource_id', None)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        # 同样移除 resource_id
        validated_data.pop('resource_id', None)
        return super().update(instance, validated_data)
    
class ResourceBindVoucherSerializer(serializers.Serializer):
    resource_id = serializers.IntegerField()
    vorcher_list = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=True,
        error_messages={
            'vorcher_list':'凭证错误,请重试'
        }
    )