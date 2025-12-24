from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from rest_framework.decorators import action
from perm.authentication import BasePermission
from .models import LoginLog,OperationLog,SessionLog
from .serialization import LoginLogSerializer,SessionLogSerializer,OperationLogSerializer
from django.db import models
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
        if self.parted:
            query = query.filter(user=request.user)
        data = OperationLogSerializer(query,many=True).data
        return Response({'code':200, 'msg': 'sucssed','data':data}, status=200)
    @action(
        methods=['post'],
        detail=False,
        url_path='session',
    )
    def session(self,request):
        #/audit/[all|self]/session/
        query = SessionLog.objects.all()
        if self.parted:
            query = query.filter(user=request.user)
        data = SessionLogSerializer(query,many=True).data
        return Response({'code':200, 'msg': 'sucssed','data':data}, status=200)
    @action(
        methods=['post'],
        detail=False,
        url_path='login',
    )
    def login(self,request):
        #/audit/[all|self]/login/
        query = LoginLog.objects.all()
        if self.parted:
            query = query.filter(user=request.user)
        data = LoginLogSerializer(query,many=True).data
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