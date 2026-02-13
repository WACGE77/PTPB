from django.db.models import Subquery
from Utils.Const import AUDIT, PERMISSIONS, METHODS, ERRMSG
from Utils.modelViewSet import create_base_view_set, CURDModelViewSet
from perm.authentication import ResourcePermission,ResourceGroupPermission
from perm.models import ResourceGroupAuth
from resource.models import Resource, Voucher, ResourceGroup
from resource.serialization import ResourceSerializer, VoucherSerializer, ResourceGroupSerializer
from audit.Logging import OperaLogging


# # Create your views here.
class _ResourceCustomizeView:

    def search(self, request):
        groups = list(ResourceGroupAuth.objects.filter(
            role__in=request.user.roles.all(),
            permission__code=PERMISSIONS.RESOURCE.SELF.READ,
        ).values_list('resource_group', flat=True))
        return self.model.objects.filter(group__id__in=groups)

_ResourceViewSet = create_base_view_set(
    Resource,
    ResourceSerializer,
[ResourcePermission],
    PERMISSIONS.RESOURCE.SELF,
    OperaLogging,
    AUDIT.CLASS.RESOURCE
)
class ResourceViewSet(_ResourceCustomizeView,_ResourceViewSet):

    def extra_data(self,data):
        groups_id = set()
        for resource in data:
            groups_id.add(resource.get('group',None))
        root_ids = ResourceGroup.objects.filter(id__in=groups_id).values_list('root',flat=True).distinct()
        groups = ResourceGroup.objects.filter(
            root__in=Subquery(root_ids),
        ).distinct()
        return ResourceGroupSerializer(groups,many=True).data

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

class ResourceGroupViewSet(CURDModelViewSet):
    permission_classes = [ResourceGroupPermission]
    protect_key = 'protected'
    model = ResourceGroup
    serializer_class = ResourceGroupSerializer
    log_class = OperaLogging
    audit_object = AUDIT.CLASS.RESOURCE_GROUP
    permission_mapping = {
        'SYSTEM':{
            METHODS.CREATE: PERMISSIONS.SYSTEM.RESOURCE_GROUP.CREATE,
            METHODS.UPDATE: PERMISSIONS.SYSTEM.RESOURCE_GROUP.UPDATE,
            METHODS.DELETE: PERMISSIONS.SYSTEM.RESOURCE_GROUP.DELETE,
            METHODS.READ: PERMISSIONS.SYSTEM.RESOURCE_GROUP.READ,
        },
        'RESOURCE':{
            METHODS.CREATE: PERMISSIONS.RESOURCE.GROUP.CREATE,
            METHODS.UPDATE: PERMISSIONS.RESOURCE.GROUP.UPDATE,
            METHODS.DELETE: PERMISSIONS.RESOURCE.GROUP.DELETE,
        }
    }

    def check(self,id_list):
        ret = dict()
        resources = list(Resource.objects.filter(group__in=id_list))
        vouchers = list(Voucher.objects.filter(group__in=id_list))
        groups = list(ResourceGroup.objects.filter(parent__in=id_list))
        all_group_ids = set()
        for resource in resources:
            all_group_ids.add(resource.group.id)
        for voucher in vouchers:
            all_group_ids.add(voucher.group.id)
        for group in groups:
            all_group_ids.add(group.id)
        RESOURCE_KEY = AUDIT.CLASS.RESOURCE
        VOUCHER_KEY = AUDIT.CLASS.VOUCHER
        GROUP_KEY = AUDIT.CLASS.RESOURCE_GROUP
        for group_id in all_group_ids:
            ret[group_id] = {
                RESOURCE_KEY: [],
                VOUCHER_KEY: [],
                GROUP_KEY: []
            }
        for resource in resources:
            ret[resource.group.id][RESOURCE_KEY].append(resource.id)
        for voucher in vouchers:
            ret[voucher.group.id][VOUCHER_KEY].append(voucher.id)
        for group in groups:
            ret[group.id][GROUP_KEY].append(group.id)
        if ret:
            prompt = ""
            for item,relations in ret.items():
                prompt += self.audit_object + str(item) + ERRMSG.RELATION.PROMPT
                for obj,ids in relations.items():
                    prompt += obj + str(ids)
                prompt += ERRMSG.RELATION.DELETE + '\n'
            return prompt
        return None