from django.db.transaction import atomic
from django.shortcuts import get_object_or_404
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework.decorators import action
from .authentication import TokenPermission, BasePermission
from rbac.models import Role,User
from .serialization import RolePermissionSerializer,BaseAuthSerializer, UserRoleSerializer
from audit.Logging import OperaLogging
# Create your views here.

# class BaseAuthManageViewSet(ViewSet):
#     permission_classes = [TokenPermission, BasePermission]
#     permission_mapping = {
#         'get_base_auth': 'permissions.role.read',
#         'mod_base_auth': 'permissions.role.update',
#     }
#     @action(detail=True, methods=['post'], url_path='get')
#     def get_base_auth(self, request, pk=None):
#         # /perm/base-auth/{pk}/get/
#         try:
#             pk = int(pk)
#         except ValueError:
#             return Response({'code':400, 'msg': '参数错误'}, status=400)
#
#         try:
#             role = Role.objects.get(id=pk)
#             serializer = RolePermissionSerializer(role)
#             data = serializer.data
#             return Response({'code':200, 'msg': '获取成功', 'data': data}, status=200)
#         except Exception:
#             return Response({'code':400, 'msg': '未找到对应的基础权限'}, status=404)
#
#     @atomic
#     @action(detail=False, methods=['post'], url_path='mod')
#     def mod_base_auth(self, request, pk=None):
#         # /perm/base-auth/mod/
#         serializer = BaseAuthSerializer(data=request.data)
#         role = request.data.get('role_id', 0)
#         perms = request.data.get('perm_ids', [])
#         opera = f"修改角色ID[{role}]的基础权限为权限ID列表{perms}"
#         if not serializer.is_valid():
#             OperaLogging.operation(request, opera, status=False)
#             return Response({'code':400, 'msg': '参数错误', 'errors': serializer.errors}, status=400)
#         role = serializer.context.get('role')
#         role.perms.set(perms)
#         OperaLogging.operation(request, opera, status=True)
#         return Response({'code':200, 'msg': '修改成功'}, status=200)

# class RoleBindManageViewSet(ViewSet):
#     permission_classes = [BasePermission]
#     permission_mapping = {
#         'get_role':"permissions.role.read",
#         'mod_role':"permissions.role.update",
#     }
#
#     @action(
#         methods=['post'],
#         detail=True,
#         url_path='get',
#     )
#     def get_role(self,request,pk):
#         #/perm/role-bind/pk/get-role/
#         user = get_object_or_404(User, id=pk)
#         roles = Role.objects.all()
#         all_roles = RoleSerializer(roles,many=True).data
#         user_role = UserRoleSerializer(user).data
#         return Response({'code':200, 'msg': '查询成功', 'data': {'all_roles': all_roles, 'user': user_role}}, status=200)
#
#     @action(
#         methods=['post'],
#         detail=True,
#         url_path='modify',
#     )
#     def mod_role(self,request,pk):
#         #/perm/role-bind/pk/modify/
#         user = get_object_or_404(User, id=pk)
#         role_serializer = RoleIDListSerializer(data=request.data)
#         role_ids = request.data.get('id_list', [])
#         opera = f'修改用户{user.account}角色为{role_ids}'
#         if role_serializer.is_valid():
#             roles = Role.objects.filter(id__in=role_ids)
#             user.roles.set(roles)
#             OperaLogging.operation(request, opera)
#             return Response({'code':200, 'msg': '用户角色修改成功'}, status=200)
#         OperaLogging.operation(request, opera, False)
#         return Response({'code':400, 'msg': role_serializer.errors}, status=400)