from rest_framework import serializers
from .models import LoginLog,OperationLog,SessionLog
from rbac.serialization import UserSerializer
from resource.serialization import ResourceSerializer

class LoginLogSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    class Meta:
        model = LoginLog
        fields = "__all__"

class OperationLogSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    class Meta:
        model = OperationLog
        fields = "__all__"
        
class SessionLogSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    resource = ResourceSerializer()
    class Meta:
        model = SessionLog
        fields = "__all__"