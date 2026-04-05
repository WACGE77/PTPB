from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework import status

from Utils.modelViewSet import create_base_view_set, CURDModelViewSet
from Utils.Const import PERMISSIONS, METHODS, AUDIT, RESPONSE__200__SUCCESS, RESPONSE__400__FAILED, KEY

from audit.Logging import OperaLogging

from .models import SSHCommandFilter
from .serialization import SSHCommandFilterSerializer
from .cache import clear_cache

# 创建SSH命令过滤规则视图集
_SSHCommandFilterViewSet = create_base_view_set(
    SSHCommandFilter,
    SSHCommandFilterSerializer,
    [],
    PERMISSIONS.SYSTEM.SSH_FILTER,
    OperaLogging,
    AUDIT.CLASS.SSH_FILTER,
)

class SSHCommandFilterViewSet(_SSHCommandFilterViewSet):
    """SSH命令过滤规则视图集"""
    
    def search(self, request):
        """搜索规则"""
        group_id = request.query_params.get('group_id')
        if group_id:
            return SSHCommandFilter.objects.filter(group__id=group_id)
        return SSHCommandFilter.objects.all()
    
    def add_or_edit(self, request, serializer, act):
        """重写添加或编辑方法，处理group_id字段"""
        instance = None
        if serializer.is_valid():
            try:
                instance = serializer.save()
                self.out_log(request, act, True)
                # 清除缓存
                clear_cache(instance.group.id)
                return instance, Response({**RESPONSE__200__SUCCESS, KEY.SUCCESS: SSHCommandFilterSerializer(instance).data}, status=status.HTTP_200_OK)
            except Exception as e:
                error_message = str(e)
                if hasattr(e, 'detail'):
                    error_message = e.detail
                return instance, Response({**RESPONSE__400__FAILED, KEY.ERROR: error_message}, status=status.HTTP_400_BAD_REQUEST)
        self.out_log(request, act, False)
        return instance, Response({**RESPONSE__400__FAILED, KEY.ERROR: serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], url_path='del')
    def delete(self, request):
        """重写删除方法，清除缓存"""
        from Utils.modelViewSet import IDListSerializer
        serializer = IDListSerializer(data=request.data)
        act = AUDIT.ACTION.DEL + self.audit_object
        if serializer.is_valid():
            id_list = serializer.data['id_list']
            remain = self.check(id_list)
            if remain:
                return Response({**RESPONSE__400__FAILED, KEY.ERROR: remain}, status=status.HTTP_400_BAD_REQUEST)
            
            # 获取要删除的规则，以便清除缓存
            rules = SSHCommandFilter.objects.filter(id__in=id_list)
            group_ids = set()
            for rule in rules:
                group_ids.add(rule.group.id)
            
            count = rules.count()
            rules.delete()
            
            # 清除缓存
            for group_id in group_ids:
                clear_cache(group_id)
            
            if count > 0:
                self.out_log(request, act, True)
                return Response({**RESPONSE__200__SUCCESS, KEY.TOTAL: count}, status=status.HTTP_200_OK)
        self.out_log(request, act, False)
        return Response({**RESPONSE__400__FAILED, KEY.ERROR: f"无删除{self.audit_object}条目"}, status=status.HTTP_400_BAD_REQUEST)
