from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from rest_framework.decorators import action
from PTPUtils.public import get_page
from perm.authentication import BasePermission
from .models import LoginLog,OperationLog,SessionLog
from .serialization import LoginLogSerializer,SessionLogSerializer,OperationLogSerializer
from django.db.models import Q
# Create your views here.
class AuditViewSet(ViewSet):
    permission_classes = [BasePermission]
    permission_mapping = {}
    parted = None
    @action(
        methods=['post'],
        detail=False,
        url_path='opera',
    )
    def operation(self,request):
        #/audit/[all|self]/opera/
        query = OperationLog.objects.all()
        key = request.data.get('key',None)
        if key:
            query = query.filter(Q(ip__icontains=key) | Q(operation__icontains=key)| Q(user__name__icontains=key))
        if self.parted:
            query = query.filter(user=request.user)
        if request.data.get('desc',False):
            query = query.order_by('-date')
        page,total = get_page(request,query)
        logs = OperationLogSerializer(page,many=True).data
        data = {
            'total':total,
            'logs':logs
        }
        return Response({'code':200, 'msg': 'sucssed','data':data}, status=200)
    @action(
        methods=['post'],
        detail=False,
        url_path='session',
    )
    def session(self,request):
        #/audit/[all|self]/session/
        query = SessionLog.objects.all()
        key = request.data.get('key',None)
        if key:
            query = query.filter(ip__icontains=key)
        if self.parted:
            query = query.filter(user=request.user)
        if request.data.get('desc',False):
            query = query.order_by('-start_time')
        page,total = get_page(request,query)
        logs = SessionLogSerializer(page,many=True).data
        data = {
            'total':total,
            'logs':logs
        }
        return Response({'code':200, 'msg': 'sucssed','data':data}, status=200)
    @action(
        methods=['post'],
        detail=False,
        url_path='login',
    )
    def login(self,request):
        #/audit/[all|self]/login/
        query = LoginLog.objects.all()
        key = request.data.get('key',None)
        if key:
            query = query.filter(Q(ip__icontains=key) | Q(user__name__icontains=key))
        if self.parted:
            query = query.filter(user=request.user)
        if request.data.get('desc',False):
            query = query.order_by('-date')
        page,total= get_page(request,query)
        logs = LoginLogSerializer(page,many=True).data
        data = {
            "total":total,
            "logs":logs
        }
        return Response({'code':200, 'msg': 'sucssed','data':data}, status=200)

class AuditALLViewSet(AuditViewSet):
    parted = False
    permission_mapping = {
        'operation':'audit.operation.read',
        'session':'audit.session.read',
        'login':'audit.operation.read',
    }
class AuditSelfViewSet(AuditViewSet):
    parted = True
    permission_mapping = {
        'operation':'user.profile.read',
        'session':'user.profile.read',
        'login':'user.profile.read',
    }