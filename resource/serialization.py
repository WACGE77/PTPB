from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from Utils.Const import ERRMSG,KEY
from resource.models import Resource, Voucher, ResourceGroup


class ResourceGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResourceGroup
        fields = '__all__'
        exclude = 'protected'
        read_only_fields = ('id','create_date','update_date')
        extra_kwargs = {
            'name':{
                'validators': [
                    UniqueValidator(
                        queryset=ResourceGroup.objects.all(),
                        message=ERRMSG.UNIQUE.NAME,
                    )
                ],
            }
        }

class ResourcePermissionSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    group = serializers.IntegerField(read_only=True)

class ResourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resource
        fields = '__all__'
        read_only_fields = ('id','create_date','update_date','vouchers')
        extra_kwargs = {
            "name":{
                'validators':[UniqueValidator(
                    queryset=Resource.objects.all(),
                    message=ERRMSG.UNIQUE.NAME
                )]
            },
            "ipv4_address":{
                "error_message":{
                    'invalid':ERRMSG.INVALID.IP,
                },
                'validators':[UniqueValidator(
                    queryset=Resource.objects.all(),
                    message=ERRMSG.UNIQUE.IPV4_ADDRESS
                )]
            },
            "ipv6_address":{
                "error_message": {
                    'invalid': ERRMSG.INVALID.IP,
                },
                'validators':[UniqueValidator(
                    queryset=Resource.objects.all(),
                    message=ERRMSG.UNIQUE.IPV6_ADDRESS
                )]
            },
        }
    def validate(self, attrs):
        if attrs.get('ipv4_address') and attrs.get('ipv6_address'):
            raise serializers.ValidationError({KEY.IP:ERRMSG.EXCLUSION.IPV4_IPV6})
        attrs['ipv4_address'] = attrs.get('ipv4_address') or None
        attrs['ipv6_address'] = attrs.get('ipv6_address') or None
        return attrs

class VoucherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Voucher
        fields = '__all__'
        read_only_fields = ('id','create_date','update_date')
        extra_kwargs = {
            "name":{
                "validators":[UniqueValidator(
                    queryset=Voucher.objects.all(),
                    message=ERRMSG.UNIQUE.NAME
                )]
            },
        }