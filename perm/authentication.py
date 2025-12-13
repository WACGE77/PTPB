from cryptography.fernet import InvalidToken
from rest_framework import permissions
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import PermissionDenied
from rest_framework_simplejwt.tokens import AccessToken
from .models import BaseAuth, ResourceAuth

from rbac.models import User
from functools import wraps


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
            return user, token
        except Exception as e:
            return None

class TokenPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated

class BasePermission(permissions.BasePermission):

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        permission_code = None
        if hasattr(view, 'action') and view.action:
            if getattr(view, 'permission_mapping', None):
                permission_code = view.permission_mapping.get(view.action, None)
            if not permission_code:
                method = getattr(view, view.action, None)
                if method:
                    permission_code = getattr(method, 'permission_code', None)

        if not permission_code:
            permission_code = getattr(view, 'permission_code', None)

        if permission_code and BaseAuth.objects.filter(permission__code=permission_code,role__in=request.user.roles.all()).exists():
            return True
        else:
            raise PermissionDenied(detail='您无当前权限',code=403)

class ResourcePermission(permissions.BasePermission):

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if hasattr(view, 'action') and view.action and view.permission_mapping:
            permission_code = view.permission_mapping.get(view.action, None)
        else:
            permission_code = view.permission_code
        base = BaseAuth.objects.filter(permission__code=permission_code,role__in=request.user.roles.all())
        if base.exists():
            return True
        resource_id = request.data.get('resource_id',0)
        adv = ResourceAuth.objects.filter(
            role__in=request.user.roles,
            permission__code=permission_code,
            resource__id=resource_id,
        )
        if resource_id and adv.exists():
            return True
        else:
            raise PermissionDenied(detail='您无当前权限',code=403)
