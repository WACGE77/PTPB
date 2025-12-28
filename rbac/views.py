from django.shortcuts import get_object_or_404
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.paginator import Paginator
from audit.Logging import OperaLogging
from perm.authentication import BasePermission
from .models import User,Role,Permission
from .serialization import LoginSerializer, ChangePasswordSerializer, ResetPasswordSerializer, \
    UserAddSerializer, UserModifySerializer, UserSerializer,RoleSerializer,PermissionSerializer,\
    RoleIDListSerializer,IDListSerializer
from .utils import verify_password, get_client_ip, get_token_response, reset_password_response


# Create your views here.

class LoginView(APIView):
    permission_classes = []
    def post(self, request):
        login_serializer = LoginSerializer(data=request.data)
        if not login_serializer.is_valid():
            return Response({'code':400, 'msg': login_serializer.errors}, status=200)
  
        account = login_serializer.validated_data.get('account')
        password = login_serializer.validated_data.get('password')
        try:
            user = User.objects.get(account=account)
        except User.DoesNotExist:
            return Response({'code':400, 'msg': '用户不存在'}, status=200)

        if verify_password(password, user.password):
            res = get_token_response(user,{'code':200, 'msg': '登录成功'})
            OperaLogging.login(get_client_ip(request), user,'succeed')
            return res
        else:
            OperaLogging.login(get_client_ip(request), user, 'failed')
            return Response({'code':400, 'msg': '密码错误'}, status=200)

class LogoutView(APIView):
    def post(self, request):
        request.META['Authorization'] = None
        response = Response({'code':200, 'msg': '退出成功'}, status=200)
        response.delete_cookie('refresh')
        return response

class RefreshView(APIView):
    permission_classes = []
    def post(self, request):
        refresh = request.COOKIES.get('refresh', None)
        try:
            token = RefreshToken(refresh)
            user_id = token['user_id']
            user = User.objects.get(id=user_id)
        except Exception:
            return Response({'code':400, 'msg': '无效的刷新请求'}, status=400)
        return get_token_response(user,{'code': 200, 'msg': '刷新成功'})

class UserManagerViewSet(ViewSet):
    permission_classes = [BasePermission]
    permission_mapping = {
        "reset_password_self": "user.profile.update",
        "reset_password": "system.user.update",
        'add_user': 'system.user.create',
        'del_user': 'system.user.delete',
        'mod_user_self':"user.profile.update",
        'mod_user':"system.user.update",
        'list_user':"system.user.read",
        'user_detail':"system.user.read",
    }

    @action(
        methods=['post'],
        detail=False,
        url_path='reset-password',
    )
    def reset_password_self(self, request):
        # /rbac/user/reset-password/
        serializer = ChangePasswordSerializer(data=request.data, context={'user': request.user})
        return reset_password_response(serializer,request)

    @action(
        methods=['post'],
        detail=True,
        url_path='reset-password',
    )
    def reset_password(self, request, pk):
        # /rbac/user/{pk}/reset-password/
        user = User.objects.get(id=pk)
        serializer = ResetPasswordSerializer(data=request.data, context={'user': user})
        return reset_password_response(serializer)

    @action(
        methods=['post'],
        detail=False,
        url_path='add',
    )
    def add_user(self,request):
        #/rbac/user/add/
        serializer = UserAddSerializer(data=request.data)
        opera = f'添加用户{request.data.get('account')}'
        if serializer.is_valid():
            serializer.save()
            OperaLogging.operation(request,opera)
            return Response({'code':200, 'msg': '添加成功'}, status=200)
        OperaLogging.operation(request, opera, False)
        return Response({'code':400, 'msg': serializer.errors}, status=400)

    @action(
        methods=['post'],
        detail=False,
        url_path='delete',
    )
    def del_user(self,request):
        #/rbac/user/delete
        serializer = IDListSerializer(data=request.data)
        ids = request.data.get('id_list', [])
        opera = f'删除用户{ids}'
        if not serializer.is_valid():
            OperaLogging.operation(request, opera, False)
            return Response({'code':400, 'msg': serializer.errors}, status=400)

        count,_ = User.objects.filter(id__in=ids,protected=False).delete()
        if count == 0:
            OperaLogging.operation(request, opera, False)
            return Response({'code':400, 'msg': '删除失败,没有符合条件的用户'}, status=400)
        OperaLogging.operation(request, opera)
        return Response({'code':200, 'msg': '删除成功','count':count}, status=200)

    @action(
        methods=['post'],
        detail=False,
        url_path='modify',
    )
    def mod_user_self(self,request):
        #/rbac/user/modify
        serializer = UserModifySerializer(request.user,data=request.data)
        opera = f'修改用户{request.user.account}'
        if serializer.is_valid():
            serializer.save()
            OperaLogging.operation(request, opera)
            return Response({'code':200, 'msg': '修改成功'}, status=200)
        OperaLogging.operation(request, opera, False)
        return Response({'code':400, 'msg': serializer.errors}, status=400)

    @action(
        methods=['post'],
        detail=True,
        url_path='modify',
    )
    def mod_user(self,request,pk):
        #/rbac/user/pk/modify
        user = User.objects.get(id=pk)
        status = request.data.get('status',None)
        serializer = UserModifySerializer(user,data=request.data)
        opera = f'修改用户{user.account}'
        if serializer.is_valid():
            if status and not user.protected:
                serializer.save(status=status)
            else:
                serializer.save()
            OperaLogging.operation(request, opera)
            return Response({'code':200, 'msg': '修改成功'}, status=200)
        OperaLogging.operation(request, opera, False)
        return Response({'code':400, 'msg': serializer.errors}, status=400)
    
    @action(
        methods=['post'],
        detail=False,
        url_path='list',
    )
    def list_user(self,request):
        #/rbac/user/list/
        try:
            page_size = request.data.get('page_size',10)
            page_number = request.data.get('page_number',1)
            users = User.objects.all()
            paginator = Paginator(users, page_size)
            page = paginator.page(page_number)
            data = UserSerializer(page.object_list,many=True).data
        except Exception:
            return Response({'code':400, 'msg': '参数错误'}, status=400)
        return Response({'code':200, 'msg': '查询成功', 'data': data}, status=200)

    

class RoleManagerViewSet(ViewSet): 
    permission_classes = [BasePermission]
    permission_mapping = {
        'add_role': 'system.role.create',
        'del_role': 'system.role.delete',
        'mod_role': 'system.role.update',
        'list_role': 'system.role.read',
    }
    @action(
        methods=['post'],
        detail=False,
        url_path='add',
    )
    def add_role(self,request):
        #/rbac/role/add/
        role = RoleSerializer(data=request.data)
        opera = f'添加角色{request.data.get("code")}'
        if role.is_valid():
            role.save()
            OperaLogging.operation(request, opera)
            return Response({'code':200, 'msg': '添加成功'}, status=200)
        OperaLogging.operation(request, opera, False)
        return Response({'code':400, 'msg': role.errors}, status=400)

    @action(
        methods=['post'],
        detail=False,
        url_path='delete',
    )
    def del_role(self,request):
        #/rbac/role/delete
        serializer = RoleIDListSerializer(data=request.data)
        ids = request.data.get('id_list', [])
        opera = f'删除角色{ids}'
        if not serializer.is_valid():
            OperaLogging.operation(request, opera, False)
            return Response({'code':400, 'msg': serializer.errors}, status=400)
        count,_ = Role.objects.filter(id__in=ids,protected=False).delete()
        if count == 0:
            OperaLogging.operation(request, opera, False)
            return Response({'code':400, 'msg': '删除失败,没有符合条件的角色'}, status=400)
        OperaLogging.operation(request, opera)
        return Response({'code':200, 'msg': '删除成功','count':count}, status=200)

    @action(
        methods=['post'],
        detail=True,
        url_path='modify',
    )
    def mod_role(self,request,pk):
        #/rbac/role/pk/modify
        opera = f'修改角色{pk}'
        try:
            role = Role.objects.get(id=pk,protected=False)
        except Role.DoesNotExist:
            OperaLogging.operation(request, opera, False)
            return Response({'code':400, 'msg': '可被修改的角色不存在'}, status=400)
        serializer = RoleSerializer(role,data=request.data)
        if serializer.is_valid():
            serializer.save()
            OperaLogging.operation(request, opera)
            return Response({'code':200, 'msg': '修改成功'}, status=200)
        OperaLogging.operation(request, opera, False)
        return Response({'code':400, 'msg': serializer.errors}, status=400)

    @action(
        methods=['post'],
        detail=False,
        url_path='list',
    )
    def list_role(self,request):
        #/rbac/role/list
        try:
            page_size = request.data.get('page_size',10)
            page_number = request.data.get('page_number',1)
            roles = Role.objects.all()
            paginator = Paginator(roles, page_size)
            page = paginator.page(page_number)
            data = RoleSerializer(page.object_list,many=True).data
        except Exception:
            return Response({'code':400, 'msg': '参数错误'}, status=400)
        return Response({'code':200, 'msg': '查询成功', 'data': data}, status=200)
    
class PermissionListView(APIView):
    permission_classes = [BasePermission]
    permission_code = 'system.perm.read'
    def post(self, request):
        # /rbac/perm/
        perms = Permission.objects.all()
        scope = request.data.get('scope', None)
        try:
            if scope:
                perms = perms.filter(scope=scope)
            data = PermissionSerializer(perms,many=True).data
            if not data:
                return Response({'code':400, 'msg': '无结果'}, status=200)
            return Response({'code':200, 'msg': '查询成功', 'data': data}, status=200)
        except Exception:
            return Response({'code':400, 'msg': '参数错误'}, status=400)
        