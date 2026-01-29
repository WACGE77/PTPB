import ipaddress

from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from Utils.Const import ERRMSG, KEY, WRITE_ONLY_FILED, CONFIG
from rbac.models import Role
from resource.models import Resource, Voucher, ResourceGroup


class ResourceGroupSerializer(serializers.ModelSerializer):
    role = serializers.PrimaryKeyRelatedField(
        write_only=True,
        queryset=Role.objects.all(),
        default=serializers.CreateOnlyDefault(None)
    )
    class Meta:
        model = ResourceGroup
        exclude = ('protected',)
        read_only_fields = ('id','create_date','update_date','level')
        extra_kwargs = {
            'name':{
                'validators': [
                    UniqueValidator(
                        queryset=ResourceGroup.objects.all(),
                        message=ERRMSG.UNIQUE.NAME,
                    )
                ],
            },
            "parent": {
                "error_messages": {
                    'does_not_exist': ERRMSG.ABSENT.GROUP,
                },
                'default':serializers.CreateOnlyDefault(None)
            },
            "root": {
                "error_messages": {
                    'does_not_exist': ERRMSG.ABSENT.GROUP,
                },
                'default': serializers.CreateOnlyDefault(None)
            },
        }


class ResourcePermissionSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    group = serializers.IntegerField(required=False)

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
            "password":WRITE_ONLY_FILED,
            "private_key":WRITE_ONLY_FILED,
        }

class ResourceSerializer(serializers.ModelSerializer):
    vouchers = VoucherSerializer(many=True,read_only=True)
    voucher_ids = serializers.PrimaryKeyRelatedField(
        queryset=Voucher.objects.all(),
        many=True,
        write_only=True,
        source='vouchers',
        required=False
    )
    class Meta:
        model = Resource
        fields = '__all__'
        read_only_fields = ('id','create_date','update_date')
        extra_kwargs = {
            "name":{
                'validators':[UniqueValidator(
                    queryset=Resource.objects.all(),
                    message=ERRMSG.UNIQUE.NAME
                )]
            },
            "ipv4_address":{
                "error_messages":{
                    'invalid':ERRMSG.INVALID.IP,
                },
                'validators':[UniqueValidator(
                    queryset=Resource.objects.all(),
                    message=ERRMSG.UNIQUE.IPV4_ADDRESS
                )]
            },
            "ipv6_address":{
                "error_messages": {
                    'invalid': ERRMSG.INVALID.IP,
                },
                'validators':[UniqueValidator(
                    queryset=Resource.objects.all(),
                    message=ERRMSG.UNIQUE.IPV6_ADDRESS
                )]
            },
            "protocol":{
                "error_messages":{
                    'invalid':ERRMSG.INVALID.PROTOCOL,
                    'required':ERRMSG.REQUIRED.PROTOCOL,
                }
            }
        }
    def validate_ipv4_address(self,value):
        if not value:
            return value
        try:
            ipaddress.IPv4Address(value)
            return value
        except ipaddress.AddressValueError:
            raise serializers.ValidationError({'ipv4_address':ERRMSG.INVALID.IP})
    def validate_ipv6_address(self,value):
        if not value:
            return value
        try:
            ipaddress.IPv6Address(value)
            return value
        except ipaddress.AddressValueError:
            raise serializers.ValidationError({'ipv6_address':ERRMSG.INVALID.IP})
    def validate(self, attrs):
        ipv4_address = attrs.get('ipv4_address',getattr(self.instance,'ipv4_address',None))
        ipv6_address = attrs.get('ipv6_address',getattr(self.instance,'ipv6_address',None))
        attrs.pop('ipv4_address', '')
        attrs.pop('ipv6_address', '')
        if ipv4_address and ipv6_address or (not ipv4_address and not ipv6_address):
            raise serializers.ValidationError({KEY.IP:ERRMSG.EXCLUSION.IPV4_IPV6})
        if ipv4_address:
            attrs['ipv4_address'] = ipv4_address
        else:
            attrs['ipv6_address'] = ipv6_address
        return attrs