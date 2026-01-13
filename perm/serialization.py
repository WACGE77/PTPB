from rest_framework import serializers
from rbac.models import Role, Permission
from rbac.serialization import UserSerializer
class RolePermissionSerializer(serializers.ModelSerializer):
    perms = serializers.SerializerMethodField()
    class Meta:
        model = Role
        fields = '__all__'
    def get_perms(self, obj):
        perms = Permission.objects.filter(base_authorizations__role=obj).distinct().values('id')
        perms_id = [perm['id'] for perm in perms]
        return perms_id

class BaseAuthSerializer(serializers.Serializer):
    role_id = serializers.IntegerField()
    perm_ids = serializers.ListField(
        child=serializers.IntegerField()
    )
    def validate(self, attrs):
        role_id = attrs.get('role_id')
        perms_ids = attrs.get('perm_ids', [])
        role = Role.objects.get(id=role_id)
        if role.protected:
            raise serializers.ValidationError({"role":"受保护角色，无法修改"})
        perms = Permission.objects.filter(id__in=perms_ids).exists()
        if not role or not perms:
            raise serializers.ValidationError({"role":'角色或权限不存在'})
        self.context['role'] = role
        return attrs

class UserRoleSerializer(UserSerializer):
    roles = serializers.SerializerMethodField()
    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields
    def get_roles(self,obj):
        roles = obj.roles.all().values('id')
        roles_id = [role['id'] for role in roles]
        return roles_id