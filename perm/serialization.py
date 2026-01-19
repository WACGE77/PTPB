from django.db import transaction
from rest_framework import serializers
from Utils.Const import KEY, ERRMSG
from perm.models import ResourceGroupAuth
from rbac.models import Role
from resource.models import ResourceGroup


class _GroupSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    permission = serializers.ListField(
        child=serializers.IntegerField(),
    )
    def validate_id(self, value):
        if not ResourceGroup.objects.filter(id=value).exists():
            raise serializers.ValidationError({KEY.ROLE: ERRMSG.ABSENT.ROLE})
        return value
    def validate_permission(self, value):
        if not all(
            isinstance(i, int) and 16 <= value <= 23
            for i in value
        ):
            raise serializers.ValidationError({KEY.PERMISSIONS: ERRMSG.ERROR.PERMISSION})
        return value
# test = {
#     "role_id":1,
#     "groups":[
#         {
#             "id":1,
#             "permissions":[1,1]
#         }
#     ]
# }
class ResourceGroupAuthSerializer(serializers.Serializer):
    role_id = serializers.IntegerField()
    groups = serializers.ListField(
        child=_GroupSerializer(),
    )
    def validate_role_id(self, value):
        if not Role.objects.filter(id=value).exists():
            raise serializers.ValidationError({KEY.ROLE: ERRMSG.ABSENT.ROLE})
        return value
    @transaction.atomic
    def save(self, **kwargs):
        role = Role.object.get(id=self.validated_data['role_id'])
        ResourceGroupAuth.objects.filter(role=role).delete()
        items = []
        for group in self.validated_data['groups']:
            group_id = group['group_id']
            for permission in group['permission']:
                items.append(ResourceGroupAuth(role_id=role, group_id=group_id, permission_id=permission))
        if items:
            ResourceGroupAuth.objects.bulk_create(
                items,
                batch_size=1000,
                ignore_conflicts=False
            )

class ResourceGroupAuthListSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResourceGroupAuth
        fields = '__all__'
        read_only_fields = '__all__'
