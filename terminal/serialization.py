from rest_framework import serializers

from Utils.Const import ERRMSG
from resource.models import Resource, Voucher


class SSHAuthSerializer(serializers.Serializer):
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
        many = True,
    )
    token = serializers.CharField(read_only=True)