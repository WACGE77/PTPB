from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView

from Utils.modelViewSet import create_base_view_set, CURDModelViewSet
from Utils.Const import PERMISSIONS, RESPONSE__200__SUCCESS, RESPONSE__400__FAILED, KEY, ERRMSG

from audit.Logging import OperaLogging
from perm.authentication import TokenPermission, TokenAuthorization

from .models import GlobalSMTPConfig, AlertMethod, AlertTemplate, ProbeRule, ProbeLog
from .serialization import GlobalSMTPConfigSerializer, AlertMethodSerializer, AlertTemplateSerializer, ProbeRuleSerializer, ProbeLogSerializer
from .filter import ProbeRuleFilter, AlertMethodFilter, AlertTemplateFilter


# 创建全局SMTP配置视图集
_GlobalSMTPConfigViewSet = create_base_view_set(
    GlobalSMTPConfig,
    GlobalSMTPConfigSerializer,
    [],
    PERMISSIONS.SYSTEM.PROBE,
    OperaLogging,
    '全局SMTP配置',
)


class GlobalSMTPConfigViewSet(_GlobalSMTPConfigViewSet):
    """全局SMTP配置视图集"""
    
    @action(detail=False, methods=['get'], url_path='current')
    def get_current(self, request):
        """获取当前使用的SMTP配置"""
        config = GlobalSMTPConfig.objects.filter(is_active=True).first()
        if not config:
            config = GlobalSMTPConfig.objects.create()
        return Response({**RESPONSE__200__SUCCESS, "detail": GlobalSMTPConfigSerializer(config).data}, status=status.HTTP_200_OK)


# 创建告警方式视图集
_AlertMethodViewSet = create_base_view_set(
    AlertMethod,
    AlertMethodSerializer,
    [],
    PERMISSIONS.SYSTEM.PROBE,
    OperaLogging,
    '告警方式',
    filterset_class=AlertMethodFilter,
)


class AlertMethodViewSet(_AlertMethodViewSet):
    """告警方式视图集"""
    
    def check(self, id_list):
        """检测告警方式是否被探针规则引用"""
        ret = dict()
        probe_rules = list(ProbeRule.objects.filter(alert_method__in=id_list))
        
        all_method_ids = set()
        for rule in probe_rules:
            all_method_ids.add(rule.alert_method.id)
        
        PROBE_RULE_KEY = '探针规则'
        for method_id in all_method_ids:
            ret[method_id] = {
                PROBE_RULE_KEY: []
            }
        
        for rule in probe_rules:
            ret[rule.alert_method.id][PROBE_RULE_KEY].append(rule.id)
        
        if ret:
            prompt = ""
            for item, relations in ret.items():
                prompt += self.audit_object + str(item) + ERRMSG.RELATION.PROMPT
                for obj, ids in relations.items():
                    prompt += obj + str(ids)
                prompt += ERRMSG.RELATION.DELETE + '\n'
            return prompt
        return None


# 创建告警模板视图集
_AlertTemplateViewSet = create_base_view_set(
    AlertTemplate,
    AlertTemplateSerializer,
    [],
    PERMISSIONS.SYSTEM.PROBE,
    OperaLogging,
    '告警模板',
    filterset_class=AlertTemplateFilter,
)


class AlertTemplateViewSet(_AlertTemplateViewSet):
    """告警模板视图集"""
    
    def check(self, id_list):
        """检测告警模板是否被探针规则引用"""
        ret = dict()
        probe_rules = list(ProbeRule.objects.filter(alert_template__in=id_list))
        
        all_template_ids = set()
        for rule in probe_rules:
            all_template_ids.add(rule.alert_template.id)
        
        PROBE_RULE_KEY = '探针规则'
        for template_id in all_template_ids:
            ret[template_id] = {
                PROBE_RULE_KEY: []
            }
        
        for rule in probe_rules:
            ret[rule.alert_template.id][PROBE_RULE_KEY].append(rule.id)
        
        if ret:
            prompt = ""
            for item, relations in ret.items():
                prompt += self.audit_object + str(item) + ERRMSG.RELATION.PROMPT
                for obj, ids in relations.items():
                    prompt += obj + str(ids)
                prompt += ERRMSG.RELATION.DELETE + '\n'
            return prompt
        return None


# 创建探针规则视图集
_ProbeRuleViewSet = create_base_view_set(
    ProbeRule,
    ProbeRuleSerializer,
    [],
    PERMISSIONS.SYSTEM.PROBE,
    OperaLogging,
    '探针规则',
    filterset_class=ProbeRuleFilter,
)


class ProbeRuleViewSet(_ProbeRuleViewSet):
    """探针规则视图集"""
    
    @action(detail=True, methods=['post'], url_path='toggle')
    def toggle(self, request, pk=None):
        """启用/禁用探针规则"""
        from rest_framework.generics import get_object_or_404
        rule = get_object_or_404(self.model, pk=pk)
        rule.is_enabled = not rule.is_enabled
        rule.save()
        self.out_log(request, '切换探针规则状态', True)
        return Response({**RESPONSE__200__SUCCESS, "detail": ProbeRuleSerializer(rule).data}, status=status.HTTP_200_OK)
    
    def check(self, id_list):
        """检测探针规则是否被探测日志引用"""
        ret = dict()
        probe_logs = list(ProbeLog.objects.filter(rule__in=id_list))
        
        all_rule_ids = set()
        for log in probe_logs:
            all_rule_ids.add(log.rule.id)
        
        PROBE_LOG_KEY = '探测日志'
        for rule_id in all_rule_ids:
            ret[rule_id] = {
                PROBE_LOG_KEY: []
            }
        
        for log in probe_logs:
            ret[log.rule.id][PROBE_LOG_KEY].append(log.id)
        
        if ret:
            prompt = ""
            for item, relations in ret.items():
                prompt += self.audit_object + str(item) + ERRMSG.RELATION.PROMPT
                for obj, ids in relations.items():
                    prompt += obj + str(ids)
                prompt += ERRMSG.RELATION.DELETE + '\n'
            return prompt
        return None


# 创建探测日志视图集
_ProbeLogViewSet = create_base_view_set(
    ProbeLog,
    ProbeLogSerializer,
    [],
    PERMISSIONS.SYSTEM.PROBE,
    OperaLogging,
    '探测日志',
)


class ProbeLogViewSet(_ProbeLogViewSet):
    """探测日志视图集"""

    def search(self, request):
        """搜索日志"""
        rule_id = request.query_params.get('rule_id')
        if rule_id:
            return ProbeLog.objects.filter(rule__id=rule_id)
        return ProbeLog.objects.all()


class TestEmailView(APIView):
    """测试邮件发送API"""
    
    authentication_classes = [TokenAuthorization]
    permission_classes = [TokenPermission]
    
    def post(self, request):
        """发送测试邮件"""
        try:
            to_email = request.data.get('to_email')
            subject = request.data.get('subject', '探针监控系统 - 测试邮件')
            content = request.data.get('content', '这是一封测试邮件，用于验证SMTP配置是否正常工作。\n\n如果您收到此邮件，说明邮件发送功能配置正确！\n\n---\n探针监控系统')
            
            if not to_email:
                return Response(
                    {**RESPONSE__400__FAILED, "detail": '请输入收件人邮箱地址'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # 简单校验邮箱格式
            import re
            email_pattern = r'^[\w\.-]+@[\w\.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, to_email):
                return Response(
                    {**RESPONSE__400__FAILED, "detail": '请输入有效的收件人邮箱地址'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            from .services.alert import AlertService
            import logging
            logger = logging.getLogger(__name__)
            
            # 获取或创建临时的告警方式对象
            test_alert_method = type('obj', (object,), {
                'to_list': [to_email],
                'name': '测试邮件'
            })()
            
            # 发送邮件，获取更详细的错误信息（兼容老接口）
            send_result = AlertService.send_email_alert(
                test_alert_method,
                subject,
                content,
                return_error=True
            )

            if isinstance(send_result, tuple):
                success, err_msg = send_result
            else:
                success = bool(send_result)
                err_msg = ''

            if success:
                logger.info(f'测试邮件发送成功: {to_email}')
                return Response({
                    **RESPONSE__200__SUCCESS,
                    "detail": {
                        'message': f'测试邮件已成功发送至 {to_email}',
                        'to_email': to_email
                    }
                }, status=status.HTTP_200_OK)
            else:
                logger.error(f'测试邮件发送失败: {to_email} - {err_msg}')
                user_msg = '邮件发送失败，请检查SMTP配置'
                if err_msg:
                    user_msg = f'{user_msg}: {err_msg}'
                return Response(
                    {**RESPONSE__400__FAILED, "detail": user_msg},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'测试邮件发送异常: {str(e)}', exc_info=True)
            return Response(
                {**RESPONSE__400__FAILED, "detail": f'发送异常: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
