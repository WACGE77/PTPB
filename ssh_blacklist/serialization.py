from rest_framework import serializers
from .models import DangerCommandRule

class DangerCommandRuleSerializer(serializers.ModelSerializer):
    group_id = serializers.IntegerField(write_only=True, required=True, source='group.id')
    
    class Meta:
        model = DangerCommandRule
        fields = ['id', 'group_id', 'pattern', 'type', 'priority', 'is_active', 'description', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        group_data = validated_data.pop('group', {})
        group_id = group_data.get('id') if isinstance(group_data, dict) else group_data
        from resource.models import ResourceGroup
        group = ResourceGroup.objects.get(id=group_id)
        validated_data['group'] = group
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        if 'group' in validated_data:
            group_data = validated_data.pop('group')
            group_id = group_data.get('id') if isinstance(group_data, dict) else group_data
            from resource.models import ResourceGroup
            group = ResourceGroup.objects.get(id=group_id)
            validated_data['group'] = group
        return super().update(instance, validated_data)
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['group_id'] = instance.group.id
        return representation
