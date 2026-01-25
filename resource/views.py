from rest_framework.decorators import action
from Utils.Const import AUDIT, PERMISSIONS, ERRMSG
from Utils.modelViewSet import create_base_view_set
from perm.authentication import ResourcePermission, ResourceEditPermission, BasePermission, TokenPermission
from perm.models import ResourceGroupAuth
from resource.models import Resource, Voucher, ResourceGroup
from resource.serialization import ResourceSerializer, VoucherSerializer, ResourceGroupSerializer
from audit.Logging import OperaLogging


# # Create your views here.
class _ResourceCustomizeView:

    @action(detail=False, methods=['post'], url_path='edit', permission_classes=[ResourceEditPermission])
    def edit(self, request):
        res = super().edit(request)
        return res

    def search(self, request):
        groups = list(ResourceGroupAuth.objects.filter(
            role__in=request.user.roles.all(),
            permission__code=PERMISSIONS.RESOURCE.SELF.READ,
        ).values_list('resource_group', flat=True))
        return self.model.objects.filter(group__id__in=groups)

    @action(detail=False, methods=['get'], url_path='get', permission_classes=[TokenPermission])
    def get(self,request):
        res = super().get(request)
        return res
_ResourceViewSet = create_base_view_set(
    Resource,
    ResourceSerializer,
[ResourcePermission],
    PERMISSIONS.RESOURCE.SELF,
    OperaLogging,
    AUDIT.CLASS.RESOURCE
)
class ResourceViewSet(_ResourceCustomizeView,_ResourceViewSet):
    pass

_VoucherViewSet = create_base_view_set(
    Voucher,
    VoucherSerializer,
[ResourcePermission],
    PERMISSIONS.RESOURCE.VOUCHER,
    OperaLogging,
    AUDIT.CLASS.VOUCHER,
)
class VoucherViewSet(_ResourceCustomizeView,_VoucherViewSet):
    pass

_ResourceGroupViewSet = create_base_view_set(
    ResourceGroup,
    ResourceGroupSerializer,
    [BasePermission],
    PERMISSIONS.SYSTEM.RESOURCE_GROUP,
    OperaLogging,
    AUDIT.CLASS.RESOURCE_GROUP,
    protect_key='protected',
)
class ResourceGroupViewSet(_ResourceGroupViewSet):

    def add_after(self, instance):
        perm = [ResourceGroupAuth(role_id=1,permission_id=i,resource_group=instance) for i in range(16,24)]
        ResourceGroupAuth.objects.bulk_create(perm)

    def check(self,id_list):
        ret = dict()
        resources = list(Resource.objects.filter(group__in=id_list))
        vouchers = list(Voucher.objects.filter(group__in=id_list))
        all_group_ids = set()
        for resource in resources:
            all_group_ids.add(resource.group.id)
        for voucher in vouchers:
            all_group_ids.add(voucher.group.id)
        RESOURCE_KEY = AUDIT.CLASS.RESOURCE
        VOUCHER_KEY = AUDIT.CLASS.VOUCHER
        for group_id in all_group_ids:
            ret[group_id] = {
                RESOURCE_KEY: [],
                VOUCHER_KEY: []
            }
        for resource in resources:
            ret[resource.group.id][RESOURCE_KEY].append(resource.id)
        for voucher in vouchers:
            ret[voucher.group.id][VOUCHER_KEY].append(voucher.id)
        return ret