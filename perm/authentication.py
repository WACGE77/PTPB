
from rest_framework import permissions
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import PermissionDenied
from rest_framework_simplejwt.tokens import AccessToken

from perm.utils import validate_resource_permission, validate_vorcher_permission
from .models import BaseAuth, ResourceAuth,ResourceVoucherAuth
from rbac.utils import get_client_ip
from rbac.models import User
from functools import wraps
from resource.models import Resource


def permission_required(code):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        wrapper.permission_code = code
        return wrapper
    return decorator


class TokenAuthorization(BaseAuthentication):
    def authenticate(self, request):
        token_str = request.META.get('HTTP_AUTHORIZATION')
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
            raise PermissionDenied(detail='未登录',code=403)
        return True
    
    def has_permission(self, request, view):
        return self.auth(request,view)

class BasePermission(TokenPermission):
    
    def get_code(self, view):
        permission_code = None
        if hasattr(view,'action') and view.action and view.permission_mapping:
            permission_code = view.permission_mapping.get(view.action, None)
        else:
            permission_code = getattr(view, 'permission_code', None)
        if not permission_code:
            raise PermissionDenied(detail='代码写错了',code=403)
        return permission_code

    def auth(self,request, view):
        super().auth(request, view)
        permission_code = self.get_code(view)
        auth = BaseAuth.objects.filter(permission__code=permission_code,role__in=request.user.roles.all()).exists()
        if not auth:
            raise PermissionDenied(detail='您无当前权限访问',code=403)
        return True,permission_code
    
    def has_permission(self, request, view):
        self.auth(request,view)
        return True

class ResourcePermission(BasePermission):
    def auth(self,request, view):
        permission_code = self.get_code(view)
        id = request.data.get('id',None)
        if not id or not Resource.objects.filter(id=id).exists():
            raise PermissionDenied(detail='无该资源',code=403)
        roles_id = request.user.roles.values('id')
        if not validate_resource_permission(request.user,roles_id,id,permission_code):
            raise PermissionDenied(detail='您无当前权限',code=403)
            
    def has_permission(self, request, view):
        self.auth(request,view)
        return True
        
class ResourceVoucherPermission(BasePermission):

    def auth(self,request, view):
        permission_code = self.get_code(view)
        id = request.data.get('id',None)
        if not id:
            raise PermissionDenied(detail='参数错误',code=403)
        roles = request.user.roles.values('id')
        if not validate_vorcher_permission(request.user,roles,id,permission_code):
            raise PermissionDenied(detail='您无当前权限',code=403)
            
    def has_permission(self, request, view):
        self.auth(request,view)
        return True
        