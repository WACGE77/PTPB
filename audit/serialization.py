from rest_framework import serializers
from .models import LoginLog,OperationLog,SessionLog
from rbac.models import User
from resource.models import Resource,Voucher

class RecordUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id",'name']
class RecordResourceSerializer(serializers.ModelSerializer):
    ip = serializers.SerializerMethodField()
    class Meta:
        model = Resource
        fields = ["id",'name','ip']
    def get_ip(self, obj):
        # 优先返回 IPv4，没有则返回 IPv6
        return obj.ipv4_address or obj.ipv6_address
    
class RecordVoucherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Voucher
        fields = ["id",'username']

#------------------------------------------------------------------------
class LoginLogSerializer(serializers.ModelSerializer):
    user = RecordUserSerializer()
    class Meta:
        model = LoginLog
        fields = "__all__"

class OperationLogSerializer(serializers.ModelSerializer):
    user = RecordUserSerializer()
    class Meta:
        model = OperationLog
        fields = "__all__"

class SessionLogSerializer(serializers.ModelSerializer):
    user = RecordUserSerializer()
    resource = RecordResourceSerializer()
    voucher = RecordVoucherSerializer()
    class Meta:
        model = SessionLog
        fields = "__all__"