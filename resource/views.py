from rest_framework.decorators import action
from Utils.Const import AUDIT, PERMISSIONS, ERRMSG
from Utils.modelViewSet import create_base_view_set
from perm.authentication import ResourcePermission, ResourceEditPermission, BasePermission
from resource.models import Resource, SSHVoucher, ResourceGroup
from resource.serialization import ResourceSerializer, SSHVoucherSerializer, ResourceGroupSerializer
from audit.Logging import OperaLogging


# # Create your views here.
class _ResourceEditView:
    @action(detail=False, methods=['post'], url_path='edit', permission_classes=[ResourceEditPermission])
    def edit(self, request):
        super().edit(request)
_ResourceViewSet = create_base_view_set(
    Resource,
    ResourceSerializer,
[ResourcePermission],
    PERMISSIONS.RESOURCE.SELF,
    OperaLogging,
    AUDIT.CLASS.RESOURCE
)

class ResourceViewSet(_ResourceEditView,_ResourceViewSet):
    pass

_SSHVoucherViewSet = create_base_view_set(
    SSHVoucher,
    SSHVoucherSerializer,
[ResourcePermission],
    PERMISSIONS.RESOURCE.VOUCHER,
    OperaLogging,
    AUDIT.CLASS.VOUCHER,
)

class SSHVoucherViewSet(_ResourceEditView,_SSHVoucherViewSet):
    pass

_ResourceGroupViewSet = create_base_view_set(
    ResourceGroup,
    ResourceGroupSerializer,
    [BasePermission],
    PERMISSIONS.SYSTEM.RESOURCE_GROUP,
    OperaLogging,
    AUDIT.CLASS.RESOURCE_GROUP,
)
class ResourceGroupViewSet(_ResourceViewSet):
    check_error = ERRMSG.REMAIN.RESOURCE_GROUP
    def check(self,id_list):
        return list(Resource.objects.filter(group__in=id_list).values_list('group', flat=True).distinct())