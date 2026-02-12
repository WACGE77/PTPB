import ipaddress

from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from Utils.Const import ERRMSG, KEY, WRITE_ONLY_FILED
from perm.models import ResourceGroupAuth
from rbac.models import Role, Permission
from resource.models import Resource, Voucher, ResourceGroup


class ResourceGroupSerializer(serializers.ModelSerializer):
    role = serializers.PrimaryKeyRelatedField(
        write_only=True,
        queryset=Role.objects.all(),
        required=False
    )
    class Meta:
        model = ResourceGroup
        exclude = ('protected',)
        read_only_fields = ('id','create_date','update_date','level','root')
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
            },
        }
    def validate(self, attrs):
        role = attrs.get('role',None)
        if role:
            user = self.context.get('request').user
            roles = [item.get('id') for item in list(user.roles.values('id'))]
            if role not in roles and 1 not in roles:
                raise serializers.ValidationError({KEY.ROLE: ERRMSG.NOT_CONTAIN.ROLE})
        return attrs

    def create(self, validated_data):
        role = validated_data.pop('role',None)
        parent = validated_data.get("parent",None)
        if not parent and not role:
            raise serializers.ValidationError(ERRMSG.REQUIRED.ROLE)
        instance = ResourceGroup.objects.create(**validated_data)
        if not parent or not instance.parent or instance == instance.parent:
            perms = Permission.objects.filter(scope='resource')
            role_auth = []
            admin_auth = [ResourceGroupAuth(role_id=1, permission=perm, resource_group=instance, protected=True) for
                          perm in perms]
            if role and role.id != 1:
                role_auth = [ResourceGroupAuth(role=role, permission=perm, resource_group=instance) for perm in perms]
            auth = admin_auth + role_auth
            ResourceGroupAuth.objects.bulk_create(auth)
        return instance

    def update(self, instance, validated_data):
        validated_data.pop('role',None)
        validated_data.pop('parent',None)
        return super().update(instance, validated_data)


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
            },
            "port": {
                "error_messages": {
                    'invalid': ERRMSG.INVALID.PORT,
                    'required': ERRMSG.REQUIRED.PORT,
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
            raise serializers.ValidationError({'ipv6_address':ERRMSG.INVALID.IP})\

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

        vouchers = attrs.get('vouchers',None)
        if not vouchers:
            return attrs
        if hasattr(self,'instance') and self.instance:
            group = self.instance.group
        else:
            group = ResourceGroup.objects.get(id = attrs.get('group'))
        root = group.root
        voucher_group = [voucher.group.id for voucher in vouchers]
        groups_query = ResourceGroup.objects.filter(id__in=voucher_group).values_list('root',flat=True)
        if len(groups_query) != 1 or groups_query[0] != root.id:
            raise serializers.ValidationError({KEY.VOUCHER: ERRMSG.SAME.GROUP})
        return attrs