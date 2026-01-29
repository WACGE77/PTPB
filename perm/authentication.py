from django.shortcuts import get_object_or_404
from rest_framework import permissions
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import PermissionDenied
from rest_framework_simplejwt.tokens import AccessToken

from Utils.Const import ERRMSG, METHODS, KEY
from resource.models import ResourceGroup
from resource.serialization import ResourcePermissionSerializer
from .models import BaseAuth, ResourceGroupAuth
from Utils.before import get_client_ip
from rbac.models import User

class TokenAuthorization(BaseAuthentication):
    def authenticate(self, request):
        token_str = request.META.get('HTTP_AUTHORIZATION')
        if token_str is None:
            return None
        try:
            token = AccessToken(token_str)
            user_id = token.payload['user_id']
            user = User.objects.get(id=user_id)
            ip = get_client_ip(request)
            info = {
                'ip': ip,
                "token":token
            }
            return user, info
        except Exception as e:
            return None

class TokenPermission(permissions.BasePermission):
    def auth(self,request,view):
        if not request.user.is_authenticated:
            raise PermissionDenied(detail='未登录',code=401)
        return True
    
    def has_permission(self, request, view):
        return self.auth(request,view)

def get_code(view):
    if hasattr(view,'permission_mapping'):
        permission_code = view.permission_mapping.get(view.action, None)
    else:
        permission_code = getattr(view, 'permission_code', None)
    if not permission_code:
        raise PermissionDenied(detail='代码写错了',code=403)
    return permission_code

class BasePermission(TokenPermission):

    def auth(self,request, view):
        super().auth(request, view)
        permission_code = get_code(view)
        auth = BaseAuth.objects.filter(permission__code=permission_code,role__in=request.user.roles.all()).exists()
        if not auth:
            raise PermissionDenied(detail='您无当前权限访问',code=403)
        return True,permission_code
    
    def has_permission(self, request, view):
        self.auth(request,view)
        return True

class ResourcePermission(TokenPermission):
    def auth(self,request,view):
        super().auth(request, view)
        permission_code = get_code(view)
        group = request.GET.get('group') or request.data.get('group')
        if not group:
            raise PermissionDenied(detail=ERRMSG.ERROR.ARG,code=403)
        root = get_object_or_404(ResourceGroup, id=group).root
        if not ResourceGroupAuth.objects.filter(
            permission__code=permission_code,
            role__in=request.user.roles.all(),
            resource_group_id=root
        ).exists():
            raise PermissionDenied(detail='您无当前权限访问',code=403)
    def has_permission(self, request, view):
        self.auth(request, view)
        return True

class ResourceEditPermission(TokenPermission):
    def auth(self,request,view):
        serializer = ResourcePermissionSerializer(data=request.data)
        if not serializer.is_valid():
            raise PermissionDenied(detail=ERRMSG.ERROR.ARG,code=403)
        pk = serializer.validated_data.get('id')
        resource = get_object_or_404(view.model, pk=pk)
        group = serializer.validated_data.get('group')
        if group is None or resource.group == group:
            root = get_object_or_404(ResourceGroup, id=group).root
            permission_code = get_code(view)
            if not ResourceGroupAuth.objects.filter(
                    permission__code=permission_code,
                    role__in=request.user.roles.all(),
                    resource_group=root
            ).exists():
                raise PermissionDenied(detail='您无当前权限访问', code=403)
            return
        if hasattr(resource,'vouchers') and resource.vouchers.exists():
            raise PermissionDenied(detail=ERRMSG.SWITCH.RELATION, code=403)
        else:
            try:
                if resource.resources.exists():
                    raise PermissionDenied(detail=ERRMSG.SWITCH.RELATION, code=403)
            except Exception:
                pass

        delete_perm_code = view.permission_const_box.DELETE
        add_perm_code = view.permission_const_box.CREATE
        if not (ResourceGroupAuth.objects.filter(
            permission__code=delete_perm_code,
            role__in=request.user.roles.all(),
            resource_group=resource.group
        ).exists() and ResourceGroupAuth.objects.filter(
            permission__code=add_perm_code,
            role__in=request.user.roles.all(),
            resource_group=group
        ).exists()):
            raise PermissionDenied(detail=ERRMSG.SWITCH.GROUP,code=403)
    def has_permission(self, request, view):
        self.auth(request, view)
        return True

class AuditPermission(TokenPermission):
    def auth(self,request,view):
        super().auth(request, view)
        scope_self = request.GET.get('self')
        query = BaseAuth.objects.filter(role__in=request.user.roles.all())
        if scope_self:
            query = query.filter(
                permission__code=view.permission_mapping.get(METHODS.READ_SELF)
            )
        else:
            query = query.filter(
                permission__code=view.permission_mapping.get(METHODS.READ_ALL)
            )
        if not query.exists():
            raise PermissionDenied(detail="您无当前权限访问",code=403)

    def has_permission(self, request, view):
        self.auth(request, view)
        return True

class ResourceGroupPermission(TokenPermission):

    def __init__(self):
        super().__init__()
        self.view = None
        self.request = None

    def system_permission(self,permission_code):
        if not BaseAuth.objects.filter(
                permission__code=permission_code,
                role__in=self.request.user.roles.all()
        ).exists():
            raise PermissionDenied(detail=ERRMSG.ERROR.PERMISSION, code=403)
    def group_permission(self,permission_code,group):
        if not ResourceGroupAuth.objects.filter(
                permission__code=permission_code,
                role__in=self.request.user.roles.all(),
                resource_group=group
        ).exists():
            raise PermissionDenied(detail=ERRMSG.ERROR.PERMISSION, code=403)
    def _has_delete_permission(self):
        id_list = self.request.data.get('id_list')
        if not id_list:
            raise PermissionDenied(detail=ERRMSG.ERROR.ARG,code=400)
        groups = ResourceGroup.objects.filter(id__in=id_list).all()
        root = [group for group in groups if group.root.id == group.id]
        lafe = [group for group in groups if group.root.id != group.id]
        if len(root):
            permission_code = self.view.permission_mapping.get(KEY.SYSTEM).get(METHODS.DELETE)
            self.system_permission(permission_code)
        if len(lafe):
            permission_code = self.view.permission_mapping.get(KEY.RESOURCE).get(METHODS.DELETE)
            self.group_permission(permission_code,lafe)
        return

    def _has_read_permission(self):
        permission_code = self.view.permission_mapping.get(KEY.SYSTEM).get(METHODS.READ)
        self.system_permission(permission_code)

    def _has_create_permission(self):
        parent_id = self.request.data.get('parent')
        if parent_id:
            parent = get_object_or_404(ResourceGroup, id=parent_id)
            permission_code = self.view.permission_mapping.get(KEY.RESOURCE).get(METHODS.CREATE)
            self.group_permission(permission_code,parent.root)
        else:
            permission_code = self.view.permission_mapping.get(KEY.SYSTEM).get(METHODS.CREATE)
            self.system_permission(permission_code)
    def _has_update_permission(self):
        group_id = self.request.data.get('id')
        if not group_id:
            raise PermissionDenied(detail=ERRMSG.ERROR.ARG,code=400)
        group = get_object_or_404(ResourceGroup, id=group_id)
        if group.root == group.id:
            permission_code = self.view.permission_mapping.get(KEY.SYSTEM).get(METHODS.UPDATE)
            self.system_permission(permission_code)
        else:
            permission_code = self.view.permission_mapping.get(KEY.SRESOURCE).get(METHODS.UPDATE)
            self.group_permission(permission_code,group.root)

    def auth(self,request,view):
        self.request = request
        self.view = view
        super().auth(request, view)
        if view.action == METHODS.READ:
            self._has_read_permission()
        elif view.action == METHODS.DELETE:
            self._has_delete_permission()
        elif view.action == METHODS.UPDATE:
            self._has_update_permission()
        else:
            self._has_create_permission()
    def has_permission(self, request, view):
        self.auth(request, view)
        return True