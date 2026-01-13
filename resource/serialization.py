from rest_framework import serializers

from audit.serialization import RecordUserSerializer
from perm.models import BaseAuth, ResourceAuth

from .models import Resource,ResourceVoucher
from Utils.public import validate_exclusive_params
class VoucherRecordSerializer(serializers.ModelSerializer):
     class Meta:
        model = ResourceVoucher
        fields = ['id','code','username']
class ResourceSerializer(serializers.ModelSerializer):
    # vouchers = serializers.PrimaryKeyRelatedField(
    #     queryset=ResourceVoucher.objects.all(),
    #     many=True,
    #     required=False,      # 👈 关键：设为非必填
    #     allow_empty=True     # 👈 允许空列表 []
    # )
    vouchers = VoucherRecordSerializer(many=True, read_only=True)
    class Meta:
        model = Resource
        fields = "__all__"
        read_only_fields = ['id']
        
    def validate(self, attrs):
        
        ipv4 = attrs.get('ipv4_address',None)
        ipv6 = attrs.get('ipv6_address',None)
        try:
            validate_exclusive_params(ipv4,ipv6)
        except ValueError:
            raise serializers.ValidationError({"error":'ipv4或ipv6必须有一个不为空,且只有一个'})
        return attrs
    def update(self, instance, validated_data):
        ipv4 = validated_data.get('ipv4_address', None)
        ipv6 = validated_data.get('ipv6_address', None)
        validated_data['ipv4_address'] = None
        validated_data['ipv6_address'] = None
        if ipv4:
            validated_data['ipv4_address'] = ipv4
        else:
            validated_data['ipv6_address'] = ipv6
        return super().update(instance, validated_data)
    
class ResourceVoucherSerializer(serializers.ModelSerializer):
    resource_id = serializers.IntegerField(required=False)

    class Meta:
        model = ResourceVoucher
        fields = "__all__"
        read_only_fields = ['id', 'create_user']  # ← 把 create_user 设为只读

    def validate(self, attrs):
        # 安全获取当前要校验的值
        try:
            password = attrs.get('password', None)
            private_key = attrs.get('private_key', None)
            validate_exclusive_params(password, private_key)
        except ValueError as e:  # 只捕获预期的 ValueError
            if self.instance:
                return attrs
            raise serializers.ValidationError({
                "error": "password 或 private_key 必须有且仅有一个不为空"
            })

        return attrs

    def create(self, validated_data):
        # 从 context 获取当前用户
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['create_user'] = request.user
        else:
            raise serializers.ValidationError("无法获取当前用户")

        # 移除 resource_id（它不属于模型字段）
        validated_data.pop('resource_id', None)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        password = validated_data.get('password', None)
        private_key = validated_data.get('private_key', None)
        validated_data['password'] = None
        validated_data['private_key'] = None
        if password:
            validated_data['password'] = password
        elif private_key:
            validated_data['private_key'] = private_key
        else:
            print("no password and private_key")
            validated_data.pop('password', None)
            validated_data.pop('private_key',None)
        return super().update(instance, validated_data)
    

class ResourceBindVoucherSerializer(serializers.Serializer):
    resource_id = serializers.IntegerField()
    voucher_list = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=True,
        error_messages={
            'vorcher_list':'凭证错误,请重试'
        }
    )