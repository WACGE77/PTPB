from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from rest_framework.views import APIView
from rest_framework.decorators import action
from PTPUtils.public import get_page
from perm.authentication import ResourcePermission,BasePermission,TokenPermission,ResourceVoucherPermission
from .serialization import ResourceSerializer,ResourceVoucherSerializer,ResourceBindVoucherSerializer
from audit.Logging import OperaLogging
from perm.utils import protect_perms, validate_resource_permission
from .models import Resource,ResourceVoucher
from perm.models import BaseAuth,ResourceVoucherAuth,ResourceAuth
from django.db.models import Q
# Create your views here.

class ResourceViewSet(ViewSet):
    permission_classes = [ResourcePermission]
    permission_mapping = {
        'add_resource':'resource.self.create',
        'del_resource':'resource.self.delete',
        'mod_resource':'resource.self.update'
    }
    @action(
        methods=['post'],
        detail=False,
        url_path='add',
        permission_classes=[BasePermission]
    )
    def add_resource(self, request):
        # /resource/resource/add/
        obj = request.data.get('code','')
        opera = f'添加资源{obj}'
        serializer = ResourceSerializer(data=request.data)
        if serializer.is_valid():
            ins = serializer.save(create_user=request.user)
            protect_perms(request.user,ins,ResourceAuth)
            OperaLogging.operation(request,opera)
            return Response({'code':200, 'msg': 'sucssed'}, status=200)
        OperaLogging.operation(request,opera,False)
        return Response({'code':400, 'msg': serializer.errors}, status=400)

    @action(
        methods=['post'],
        detail=False,
        url_path='delete',
    )
    def del_resource(self, request):
        # /resource/resource/delete/
        id = request.data.get('id','')
        opera = f'删除资源{id}'
        try:
            Resource.objects.filter(id=id).delete()
        except Exception as e:
            print(e)
            OperaLogging.operation(request,opera,False)
            return Response({'code':400, 'msg': '删除失败,参数错误'}, status=400)
        OperaLogging.operation(request,opera)
        return Response({'code':200, 'msg': '删除成功'}, status=200)
    
    @action(
        methods=['post'],
        detail=False,
        url_path='modify',
    )
    def mod_resource(self, request):
        # /resource/resource/modify/
        resource_id = request.data.get('id',0)
        if not resource_id:
            return Response({'code':400, 'msg': '参数错误'}, status=400)
        instance = get_object_or_404(Resource, id=resource_id)
        opera = f'修改资源{id}'
        serializer = ResourceSerializer(instance,data = request.data,partial=True)
        if serializer.is_valid():
            serializer.save()
            OperaLogging.operation(request,opera)
            return Response({'code':200, 'msg': '修改成功'}, status=200)
        OperaLogging.operation(request,opera,False)
        
        return Response({'code':400, 'msg': serializer.errors}, status=400)
    
    @action(
        methods=['post'],
        detail=False,
        url_path='list',
        permission_classes=[TokenPermission]
    )
    def list_resource(self, request):
        # /resource/resource/list/
        resource = Resource.objects.all()
        roles = request.user.roles.all()
        if not BaseAuth.objects.filter(permission__code='resource.self.read',role__in=roles).exists():
            resource = resource.filter(
                Q(resource_authorizations__user=request.user) | 
                Q(resource_authorizations__role__in=roles)
            )
            resource = resource.filter(
                resource_authorizations__permission__code = 'resource.self.read'
            )
        if request.data.get('all',False):
            page = resource
            total = resource.count()
        else:
            page,total = get_page(request,resource)
        try:
            resources = ResourceSerializer(page,many=True).data
            data = {
                'total':total,
                'resources':resources
            }
        except Exception as e:
            return Response({'code':400, 'msg': '查询失败'}, status=400)
        return Response({'code':200, 'data':data, 'msg': 'sucssed'}, status=200)

class ResourceVoucherViewSet(ViewSet):
    
    permission_classes = [ResourceVoucherPermission]
    permission_mapping = {
        'add_resourcevoucher':'resource.voucher.create',
        'del_resourcevoucher':'resource.voucher.delete',
        'mod_resourcevoucher':'resource.voucher.update',
    }
    @action(
        methods=['post'],
        detail=False,
        url_path='add',
        permission_classes=[BasePermission]
    )
    def add_resourcevoucher(self, request):
        # /resource/voucher/add/
        obj = request.data.get('code','')
        opera = f'添加凭证{obj}'
        serializer = ResourceVoucherSerializer(data=request.data,context={'request': request})
        if serializer.is_valid():
            ins = serializer.save()
            protect_perms(request.user,ins,ResourceVoucherAuth,'voucher_all')
            resource_id = serializer.validated_data.get('resource_id',None)
            if resource_id:
                roles = request.user.roles.values('id')
                if validate_resource_permission(request.user,roles,resource_id,'resource.self.read'):
                    resource = Resource.objects.get(id=resource_id)
                    resource.vouchers.add(ins)
            OperaLogging.operation(request,opera)
            return Response({'code':200, 'msg': 'sucssed'}, status=200)
        OperaLogging.operation(request,opera,False)
        return Response({'code':400, 'msg': serializer.errors}, status=200)

    @action(
        methods=['post'],
        detail=False,
        url_path='delete',
    )
    def del_resourcevoucher(self, request):
        # /resource/voucher/delete/
        id = request.data.get('id','')
        opera = f'删除凭证{id}'
        try:
            count,_ = ResourceVoucher.objects.filter(id=id).delete()
            if count == 0:
                return Response({'code':400, 'msg': '无删除内容'}, status=400)
        except Exception:
            OperaLogging.operation(request,opera,False)
            return Response({'code':400, 'msg': '删除失败,参数错误'}, status=400)
        OperaLogging.operation(request,opera)
        return Response({'code':200, 'msg': '删除成功'}, status=200)
    
    @action(
        methods=['post'],
        detail=False,
        url_path='modify',
    )
    def mod_resourcevoucher(self, request):
        # /resource/voucher/modify/
        voucher_id = request.data.get('id',0)
        if not voucher_id:
            return Response({'code':400, 'msg': '参数错误'}, status=400)
        instance = get_object_or_404(ResourceVoucher, id=voucher_id)
        opera = f'修改凭证{voucher_id}'
        serializer = ResourceVoucherSerializer(instance,data = request.data,partial=True)
        if serializer.is_valid():
            serializer.save()
            OperaLogging.operation(request,opera)
            return Response({'code':200, 'msg': '修改成功'}, status=200)
        OperaLogging.operation(request,opera,False)
        return Response({'code':400, 'msg': serializer.errors}, status=400)
    
    @action(
        methods=['post'],
        detail=False,
        url_path='list',
        permission_classes=[TokenPermission]
    )
    def list_resourcevoucher(self, request):
        # /resource/voucher/list/
        voucher = ResourceVoucher.objects.all()
        roles = request.user.roles.all()
        key = request.data.get('key',None)
        if key:
            voucher = voucher.filter(code__icontains=key)
        if not BaseAuth.objects.filter(permission__code='resource.voucher.read',role__in=roles).exists():
            voucher = voucher.filter(
                Q(account_authorizations__user=request.user) | 
                Q(account_authorizations__role__in=roles)
            )
            voucher = voucher.filter(
                account_authorizations__permission__code = 'resource.voucher.read'
            )
        if request.data.get('all',False):
            page = voucher
            total = voucher.count()
        else:
            page,total=get_page(request,voucher)
        try:
            vouchers = ResourceVoucherSerializer(page,many=True).data
            data = {
                'total':total,
                'vouchers':vouchers
            }
        except Exception:
            return Response({'code':400, 'msg': '查询失败'}, status=400)
        return Response({'code':200, 'data':data, 'msg': 'sucssed'}, status=200)
    
class ResourceBindVoucherView(APIView):
    permission_classe = [ResourcePermission]
    permission_code = ''
    """
    {
        'resource_id':int,
        'voucher_list':[int,]
    }
    """
    def post(self,request):
        serializer = ResourceBindVoucherSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({'code':400, 'msg': serializer.errors}, status=400)
        roles = request.user.roles.all()
        ids = serializer.validated_data['voucher_list']
        resource_id = serializer.validated_data['resource_id']
        has_global_perm = BaseAuth.objects.filter(
            role__in=roles,
            permission__code='resource.voucher.read'
        ).exists()
        if not has_global_perm:
            permitted_voucher_ids = set()
            role_voucher_ids = ResourceVoucherAuth.objects.filter(
                role__in=roles,
                permission__code='resource.voucher.read'
            ).values_list('voucher_id', flat=True)
            user_voucher_ids = ResourceVoucherAuth.objects.filter(
                user=request.user,
                permission__code='resource.voucher.read'
            ).values_list('voucher_id', flat=True)
            permitted_voucher_ids.update(role_voucher_ids)
            permitted_voucher_ids.update(user_voucher_ids)
            missing = set(ids) - permitted_voucher_ids
            if missing:
                return Response({
                    'code': 400,
                    'msg': f'缺少凭证权限: {sorted(missing)}'
                }, status=400)
        resource = Resource.objects.get(id=resource_id)
        vouchers = resource.vouchers.values('id')
        vouchers_id_list = [voucher['id'] for voucher in vouchers]
        try:
            resource.vouchers.set(set(ids + vouchers_id_list))
            return Response({'code':200, 'msg': '添加成功'}, status=200)
        except Exception:
            return Response({'code':400, 'msg':'操作错误,请重试'}, status=400)
