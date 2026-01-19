from typing import Optional,Type

from django.core.paginator import Paginator, PageNotAnInteger
from django.db.models import Model
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.fields import BooleanField
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer,Serializer,ListSerializer,IntegerField
from rest_framework.viewsets import ViewSet
from box import Box

from Utils.Const import KEY, RESPONSE, ERRMSG, AUDIT, RESPONSE__200__SUCCESS, RESPONSE__400__FAILED, METHODS
from audit.Logging import OperaLogging

class IDSerializer(Serializer):
    id = IntegerField(min_value=1,error_messages={
        "invalid":ERRMSG.INVALID.ID,
        "required":ERRMSG.REQUIRED.ID,
    })

class IDListSerializer(Serializer):
    id_list = ListSerializer(
        child = IntegerField(min_value=1,error_messages={
            "invalid":ERRMSG.INVALID.ID,
            "required":ERRMSG.REQUIRED.ID,
        }),
        allow_null = False,
        error_messages={
            "invalid":ERRMSG.INVALID.ID_LIST,
            "required":ERRMSG.REQUIRED.ID_LIST,
        }
    )

class PageArg(Serializer):
    all = BooleanField(required=False)
    page_number = IntegerField(required=False,min_value=1)
    page_size = IntegerField(required=False,min_value=1)

    def validate(self, attrs):
        if not attrs.get('all'):
            attrs.setdefault('page_number', 1)
            attrs.setdefault('page_size', 10)
        return attrs


class ModelViewSet(ViewSet):
    permission_classes:list[Type[BasePermission]] = None
    protect_key: str = None
    delete_key: str = 'id_list'
    model: Model = None
    serializer_class: Optional[Type[BaseSerializer]] = None
    log_class: Optional[Type[OperaLogging]] | None = None
    audit_object: str = None
    permission_mapping = dict()
    permission_code = None
    permission_const_box:Box = None
    #relation_serializer_class = None
    #relation_audit_object: str = None
    """
    permission_classes:list 鉴权类
    protect_key:str 数据库如有受保护的数据,设置改字段
    delete_key:str 前端发来的id列表的key
    model:Model 视图集所操作的模型
    serializer_class:Optional[Type[BaseSerializer]] 视图集所指定的序列化器,需高度适应
    log_class:Optional[Callable[[object],None]] 日志记录操作类
    audit_object:str 操作对象,种类用于日志的生成
    permission_mapping: 细分权限时映射(优先级高)
    permission_code: 无需细分权限时的权限
    permission_const_box:Box 自定义常量里的权限包含CURD权限码
    ####################需要时自行添加字段#######################
    relation_serializer_class:Optional[Type[BaseSerializer]] 多对多关系下的序列化器
    relation_audit_object: 多对多关系操作对象
    """
    def out_log(self,request,act,result):
        if self.log_class:
            self.log_class.operation(request, act, result)

    def add_or_edit(self,request,serializer,act):
        instance = None
        if serializer.is_valid():
            instance = serializer.save()
            self.out_log(request,act,True)
            return instance,Response({**RESPONSE__200__SUCCESS}, status=status.HTTP_200_OK)
        self.out_log(request,act, False)
        return instance,Response({**RESPONSE__400__FAILED,KEY.ERROR:serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

class CModelViewSet(ModelViewSet):

    def add_callback(self,instance):
        pass
    @action(detail=False, methods=['post'], url_path='add')
    def add(self, request):
        serializer = self.serializer_class(data=request.data)
        act = AUDIT.ACTION.ADD + self.audit_object
        instance,res = self.add_or_edit(request, serializer, act)
        if instance:
            self.add_callback(instance)
        return res

class UModelViewSet(ModelViewSet):

    def edit_callback(self,instance):
        pass
    def is_protected(self,instance):
        return self.protect_key and hasattr(self.model, self.protect_key) and getattr(instance, self.protect_key)

    @action(detail=False, methods=['post'], url_path='edit')
    def edit(self, request):
        pk = request.data.get('id')
        act = AUDIT.ACTION.EDIT + self.audit_object + str(pk)
        instance = get_object_or_404(self.model, pk=pk)
        if self.is_protected(instance):
            return Response({**RESPONSE__400__FAILED, KEY.ERROR: ERRMSG.PROTECTED}, status=status.HTTP_400_BAD_REQUEST)
        serializer = self.serializer_class(instance, data=request.data, partial=True)
        instance,res = self.add_or_edit(request, serializer, act)
        if instance:
            self.edit_callback(instance)
        return res

class RModelViewSet(ModelViewSet):
    def search(self):
        return self.model.objects.all()
    @action(detail=False, methods=['get'], url_path='get')
    def get(self, request):
        serializer = PageArg(data=request.data)
        if serializer.is_valid():
            try:
                query = self.search()
                page_size = min(serializer.validated_data[KEY.PAGE_SIZE], 100)
                paginator = Paginator(query, page_size)
                total = paginator.count
                page = paginator.page(serializer.validated_data[KEY.PAGE_NUMBER]).object_list
                data = {
                    **RESPONSE__200__SUCCESS,
                    KEY.TOTAL: total,
                    KEY.SUCCESS: self.serializer_class(page, many=True).data,
                }
                return Response(data, status=status.HTTP_200_OK)
            except PageNotAnInteger:
                pass
        return Response({**RESPONSE__400__FAILED, KEY.ERROR: serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

class DModelViewSet(ModelViewSet):
    check_error:str = None
    def check(self,id_list):
        return False
    @action(detail=False, methods=['post'], url_path='del')
    def delete(self, request):
        serializer = IDListSerializer(data=request.data)
        act = AUDIT.ACTION.DEL + self.audit_object
        if serializer.is_valid():
            id_list = serializer.data['id_list']
            remain = self.check(id_list)
            if remain:
                return Response({**RESPONSE__400__FAILED, KEY.ERROR: f"{remain}{self.check_error}"}, status=status.HTTP_400_BAD_REQUEST)
            queryset = self.model.objects.filter(id__in=id_list)
            if self.protect_key and hasattr(self.model, self.protect_key):
                queryset = queryset.exclude(**{self.protect_key: True})
            count, _ = queryset.delete()
            if count > 0:
                self.out_log(request, act, True)
                return Response({**RESPONSE__200__SUCCESS}, status=status.HTTP_200_OK)
        self.out_log(request, act, False)
        return Response({**RESPONSE__400__FAILED, KEY.ERROR: serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

class CURDModelViewSet(CModelViewSet,UModelViewSet,RModelViewSet,DModelViewSet):
    pass


def create_base_view_set(
    model,#: Model,
    serializer_class: Type[BaseSerializer],
    permission_class: list[Type[BasePermission]],
    permission_const_box,
    log_class: Optional[Type[OperaLogging]] | None,
    audit_object: str = None,
    protect_key:str = None,
    permission_code:str = None,
    delete_key: str = 'id_list'
):
    class_name = f"_{model.__name__}ViewSet"
    perm_mapping = {
        METHODS.CREATE: permission_const_box.CREATE,
        METHODS.UPDATE: permission_const_box.UPDATE,
        METHODS.DELETE: permission_const_box.DELETE,
        METHODS.READ: permission_const_box.READ,
    }
    perm_code = permission_code
    return type(class_name, (CURDModelViewSet,), {
        'model': model,
        'serializer_class': serializer_class,
        'permission_class': permission_class,
        'log_class': log_class,
        'audit_object': audit_object,
        'permission_mapping': perm_mapping,
        'permission_const_box':permission_const_box,
        'perm_code': perm_code,
        'protect_key': protect_key,
        'delete_key': delete_key,
    })
