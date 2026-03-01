from django.views.decorators.http import condition
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from audit.Logging import OperaLogging
from perm.authentication import BasePermission, TokenPermission, RefreshAuthorization, TokenAuthorization
from .filter import UserFilter, RoleFilter
from .models import User,Role,Permission
from .serialization import LoginSerializer, ChangePasswordSerializer, \
    UserSerializer, PermissionSerializer, RoleSerializer, RolePermissionSerializer, UserRoleSerializer

from Utils.modelViewSet import CURDModelViewSet, create_base_view_set
from Utils.before import verify_password, get_token_response
from Utils.Const import PERMISSIONS,METHODS,AUDIT,RESPONSE__200__SUCCESS, \
    RESPONSE__400__FAILED, KEY, RESPONSE, ERRMSG
# Create your views here.

class LoginView(APIView):
    permission_classes = []
    def post(self, request):
        login_serializer = LoginSerializer(data=request.data)
        if not login_serializer.is_valid():
            return Response({**RESPONSE__400__FAILED, KEY.ERROR: login_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
  
        account = login_serializer.validated_data.get('account')
        password = login_serializer.validated_data.get('password')

        user = get_object_or_404(User, account=account)
        request.user = user
        if not user.status:
            raise PermissionDenied(detail=ERRMSG.ERROR.DISABLED)

        if not verify_password(password, user.password):
            OperaLogging.login(request, 'failed')
            return Response({
                **RESPONSE.P_401_UNAUTHORIZED,
                KEY.ERROR: ERRMSG.ERROR.PASSWORD
            }, status=status.HTTP_401_UNAUTHORIZED)

        res = get_token_response(user,{**RESPONSE__200__SUCCESS})
        OperaLogging.login(request,'succeed')
        return res

class LogoutView(APIView):
    permission_classes = [TokenPermission]
    def post(self, request):
        request.META['Authorization'] = None
        response = Response(RESPONSE__200__SUCCESS, status=status.HTTP_200_OK)
        response.delete_cookie('refresh')
        return response

class RefreshView(APIView):
    authentication_classes = [RefreshAuthorization]
    permission_classes = []
    def post(self, request):
        refresh = request.COOKIES.get('refresh', None)
        try:
            token = RefreshToken(refresh)
            user_id = token['user_id']
            user = User.objects.get(id=user_id)
        except Exception:
            return Response({**RESPONSE__400__FAILED}, status=401)
        return get_token_response(user, {**RESPONSE__200__SUCCESS})

_UserManagerViewSet = create_base_view_set(
    User,
    UserSerializer,
[BasePermission],
    PERMISSIONS.SYSTEM.USER,
    OperaLogging,
    AUDIT.CLASS.USER,
    protect_key='protected',
    filterset_class=UserFilter,
)
class UserManagerViewSet(_UserManagerViewSet):
    permission_mapping = {
        **_UserManagerViewSet.permission_mapping,
        "reset_password":PERMISSIONS.USER.PROFILE.UPDATE,
        "detail_":PERMISSIONS.USER.PROFILE.READ,
        "bind":PERMISSIONS.SYSTEM.PERMISSIONS.UPDATE,
    }
    @action(detail=False, methods=['post'],url_path='reset_password')
    def reset_password(self, request):
        serializer = ChangePasswordSerializer(data=request.data,context={'user': request.user})
        if serializer.is_valid():
            serializer.save()
            return Response({**RESPONSE__200__SUCCESS}, status=status.HTTP_200_OK)
        return Response({**RESPONSE__400__FAILED,KEY.ERROR:serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    @action(detail=False, methods=['get'],url_path='detail')
    def detail_(self,request):
        detail = UserSerializer(request.user).data
        detail[KEY.IP] = request.auth.get('ip')
        return Response({**RESPONSE__200__SUCCESS,KEY.SUCCESS:detail}, status=status.HTTP_200_OK)
    @action(detail=False, methods=['post'],url_path='role')
    def bind(self,request):
        pk = request.data.get('id')
        user = get_object_or_404(User, id=pk)
        if user.protected:
            return Response({**RESPONSE__400__FAILED,KEY.ERROR:ERRMSG.PROTECTED}, status=status.HTTP_400_BAD_REQUEST)
        bind_serializer = UserRoleSerializer(user,data=request.data,partial=True)
        if bind_serializer.is_valid():
            bind_serializer.save()
            return Response({**RESPONSE__200__SUCCESS}, status=status.HTTP_200_OK)
        return Response({**RESPONSE__400__FAILED,KEY.ERROR:bind_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
_RoleManagerViewSet = create_base_view_set(
    Role,
    RoleSerializer,
[BasePermission],
    PERMISSIONS.SYSTEM.ROLE,
    OperaLogging,
    AUDIT.CLASS.ROLE,
    protect_key='protected',
    filterset_class=RoleFilter,
)
class RoleManagerViewSet(_RoleManagerViewSet):
    many_serializer_class = RolePermissionSerializer
    permission_mapping = {
        **_RoleManagerViewSet.permission_mapping,
        METHODS.READ_RELATION:PERMISSIONS.SYSTEM.PERMISSIONS.READ,
        METHODS.EDIT_RELATION:PERMISSIONS.SYSTEM.PERMISSIONS.UPDATE,
    }
    relation_serializer_class = RolePermissionSerializer
    relation_audit_object: str = AUDIT.CLASS.PERMISSION

    @action(detail=False, methods=['get'], url_path=f'get/permission')
    def get_relations(self, request):
        pk = request.query_params.get('id')
        instance = get_object_or_404(self.model, pk=pk)
        many_col = self.relation_serializer_class(instance).data
        return Response({**RESPONSE__200__SUCCESS, KEY.SUCCESS: many_col}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='edit/permission')
    def edit_relations(self, request):
        pk = request.data.get('id')
        instance = get_object_or_404(self.model, pk=pk)
        if self.is_protected(instance):
            return Response({**RESPONSE__400__FAILED, KEY.ERROR: ERRMSG.PROTECTED}, status=status.HTTP_400_BAD_REQUEST)
        act = AUDIT.ACTION.EDIT + self.audit_object + str(pk) + self.relation_audit_object
        serializer = self.relation_serializer_class(instance,data=request.data)
        _,res = self.add_or_edit(request, serializer, act)
        return res

class PermissionListView(APIView):
    permission_classes = [BasePermission]
    permission_code = PERMISSIONS.SYSTEM.PERMISSIONS.READ
    def get(self, request):
        perms = PermissionSerializer(Permission.objects.all(),many=True).data
        return Response({**RESPONSE__200__SUCCESS,KEY.SUCCESS:perms}, status=status.HTTP_200_OK)

class DynamicRoutesView(APIView):
    authentication_classes = [TokenAuthorization]  # 添加认证类
    permission_classes = [TokenPermission]  # 恢复权限验证
    def get(self, request):
        # 从数据库查询所有启用的路由
        from .models import Route
        routes = Route.objects.filter(status=True).order_by('order')
        
        # 构建路由树
        route_dict = {}
        root_routes = []
        
        # 首先创建所有路由的route_data并添加到route_dict中
        for route in routes:
            route_data = {
                "path": route.path,
                "component": route.component,
                "meta": {
                    "title": route.title,
                    "icon": route.icon,
                    "permission": route.permission_code
                },
                "children": []
            }
            route_dict[route.id] = route_data
        
        # 然后构建路由树
        for route in routes:
            if route.parent_id is None:
                root_routes.append(route_dict[route.id])
            else:
                if route.parent_id in route_dict:
                    route_dict[route.parent_id]["children"].append(route_dict[route.id])
        
        # 获取用户拥有的权限
        user_permissions = set()
        from perm.models import BaseAuth, ResourceGroupAuth
        for role in request.user.roles.all():
            # 通过BaseAuth表获取权限
            auths = BaseAuth.objects.filter(role=role)
            for auth in auths:
                user_permissions.add(auth.permission.code)
            # 通过ResourceGroupAuth表获取权限
            resource_auths = ResourceGroupAuth.objects.filter(role=role)
            for auth in resource_auths:
                user_permissions.add(auth.permission.code)
        
        # 过滤路由
        def filter_routes(routes_list):
            filtered = []
            for route in routes_list:
                if "children" in route and route["children"]:
                    filtered_children = filter_routes(route["children"])
                    if filtered_children:
                        route["children"] = filtered_children
                        filtered.append(route)
                else:
                    permission = route.get("meta", {}).get("permission")
                    if permission:
                        # 直接检查用户是否有对应的权限码
                        if permission in user_permissions:
                            filtered.append(route)
                    else:
                        # 没有权限要求的路由直接添加
                        filtered.append(route)
            return filtered
        
        # 过滤路由
        filtered_routes = filter_routes(root_routes)
        
        return Response({**RESPONSE__200__SUCCESS, KEY.SUCCESS: filtered_routes}, status=status.HTTP_200_OK)
        