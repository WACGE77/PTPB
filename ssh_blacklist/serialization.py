from rest_framework import serializers
from .models import SSHCommandFilter

class SSHCommandFilterSerializer(serializers.ModelSerializer):
    """SSH命令过滤规则序列化器"""
    group_id = serializers.IntegerField(write_only=True, required=True)
    
    class Meta:
        model = SSHCommandFilter
        fields = ['id', 'group_id', 'pattern', 'type', 'priority', 'description', 'create_date', 'update_date']
    
    def create(self, validated_data):
        """创建规则"""
        group_id = validated_data.pop('group_id')
        from resource.models import ResourceGroup
        group = ResourceGroup.objects.get(id=group_id)
        validated_data['group'] = group
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        """更新规则"""
        if 'group_id' in validated_data:
            group_id = validated_data.pop('group_id')
            from resource.models import ResourceGroup
            group = ResourceGroup.objects.get(id=group_id)
            validated_data['group'] = group
        return super().update(instance, validated_data)
    
    def to_representation(self, instance):
        """序列化时添加group_id字段"""
        representation = super().to_representation(instance)
        representation['group_id'] = instance.group.id
        return representation
