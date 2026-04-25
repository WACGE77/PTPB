from rest_framework import serializers
from .models import GlobalSMTPConfig, AlertMethod, AlertTemplate, ProbeRule, ProbeLog


class GlobalSMTPConfigSerializer(serializers.ModelSerializer):
    """全局SMTP配置序列化器"""
    class Meta:
        model = GlobalSMTPConfig
        fields = ['id', 'smtp_host', 'smtp_port', 'smtp_username', 'smtp_password', 'smtp_ssl', 'is_active', 'created_at', 'updated_at']


class AlertMethodSerializer(serializers.ModelSerializer):
    """告警方式序列化器"""
    class Meta:
        model = AlertMethod
        fields = ['id', 'name', 'type', 'to_list', 'created_at', 'updated_at']


class AlertTemplateSerializer(serializers.ModelSerializer):
    """告警模板序列化器"""
    class Meta:
        model = AlertTemplate
        fields = ['id', 'name', 'title', 'content', 'created_at', 'updated_at']


class ProbeRuleSerializer(serializers.ModelSerializer):
    """探针规则序列化器"""
    alert_method_name = serializers.CharField(source='alert_method.name', read_only=True)
    alert_template_name = serializers.CharField(source='alert_template.name', read_only=True)
    
    class Meta:
        model = ProbeRule
        fields = [
            'id', 'name', 'target_type', 'target', 'detect_interval', 
            'fail_threshold', 'alert_interval', 'is_enabled', 'alert_method', 'alert_method_name',
            'alert_template', 'alert_template_name', 'last_status', 
            'last_check_at', 'last_alert_sent_at', 'consecutive_fail', 'created_at', 'updated_at'
        ]
    
    def create(self, validated_data):
        """创建探针规则时设置默认状态"""
        validated_data['last_status'] = 'up'
        return super().create(validated_data)


class ProbeLogSerializer(serializers.ModelSerializer):
    """探测日志序列化器"""
    rule_name = serializers.CharField(source='rule.name', read_only=True)
    
    class Meta:
        model = ProbeLog
        fields = ['id', 'rule', 'rule_name', 'status', 'latency', 'message', 'created_at']
