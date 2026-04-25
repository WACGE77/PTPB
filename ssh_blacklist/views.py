from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework import status

from Utils.modelViewSet import create_base_view_set, CURDModelViewSet
from Utils.Const import PERMISSIONS, METHODS, AUDIT, RESPONSE__200__SUCCESS, RESPONSE__400__FAILED, KEY

from audit.Logging import OperaLogging

from .models import DangerCommandRule
from .serialization import DangerCommandRuleSerializer
from .cache import clear_cache

_DangerCommandRuleViewSet = create_base_view_set(
    DangerCommandRule,
    DangerCommandRuleSerializer,
    [],
    PERMISSIONS.SYSTEM.DANGER_CMD,
    OperaLogging,
    AUDIT.CLASS.DANGER_CMD,
)

class DangerCommandRuleViewSet(_DangerCommandRuleViewSet):
    """危险命令告警规则视图集"""
    
    def search(self, request):
        group_id = request.query_params.get('group_id')
        if group_id:
            return DangerCommandRule.objects.filter(group__id=group_id)
        return DangerCommandRule.objects.all()
    
    def add_or_edit(self, request, serializer, act):
        instance = None
        if serializer.is_valid():
            try:
                instance = serializer.save()
                self.out_log(request, act, True)
                clear_cache(instance.group.id)
                return instance, Response({**RESPONSE__200__SUCCESS, KEY.SUCCESS: DangerCommandRuleSerializer(instance).data}, status=status.HTTP_200_OK)
            except Exception as e:
                error_message = str(e)
                if hasattr(e, 'detail'):
                    error_message = e.detail
                return instance, Response({**RESPONSE__400__FAILED, KEY.ERROR: error_message}, status=status.HTTP_400_BAD_REQUEST)
        self.out_log(request, act, False)
        return instance, Response({**RESPONSE__400__FAILED, KEY.ERROR: serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], url_path='del')
    def delete(self, request):
        from Utils.modelViewSet import IDListSerializer
        serializer = IDListSerializer(data=request.data)
        act = AUDIT.ACTION.DEL + self.audit_object
        if serializer.is_valid():
            id_list = serializer.data['id_list']
            remain = self.check(id_list)
            if remain:
                return Response({**RESPONSE__400__FAILED, KEY.ERROR: remain}, status=status.HTTP_400_BAD_REQUEST)
            
            rules = DangerCommandRule.objects.filter(id__in=id_list)
            group_ids = set()
            for rule in rules:
                group_ids.add(rule.group.id)
            
            count = rules.count()
            rules.delete()
            
            for group_id in group_ids:
                clear_cache(group_id)
            
            if count > 0:
                self.out_log(request, act, True)
                return Response({**RESPONSE__200__SUCCESS, KEY.TOTAL: count}, status=status.HTTP_200_OK)
        self.out_log(request, act, False)
        return Response({**RESPONSE__400__FAILED, KEY.ERROR: f"无删除{self.audit_object}条目"}, status=status.HTTP_400_BAD_REQUEST)
