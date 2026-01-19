from rest_framework import status
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from perm.authentication import BaseAuthentication
from Utils.Const import RESPONSE__200__SUCCESS, RESPONSE__400__FAILED, KEY, ERRMSG, METHODS, PERMISSIONS
from perm.models import ResourceGroupAuth
from perm.serialization import ResourceGroupAuthSerializer, ResourceGroupAuthListSerializer
from rbac.models import Role


# Create your views here.

class AuthorizationViewSet(ViewSet):
    permission_classes = [BaseAuthentication]
    permission_mapping = {
        METHODS.GET:PERMISSIONS.SYSTEM.PERMISSIONS.READ,
        METHODS.EDIT: PERMISSIONS.SYSTEM.PERMISSIONS.EDIT,
    }
    @action(detail=False, methods=['get'],url_name='get')
    def get(self,request):
        role_id = request.query_params.get('role_id')
        role = get_object_or_404(Role, id=role_id)
        permissions = ResourceGroupAuth.objects.filter(role=role)
        detail = ResourceGroupAuthListSerializer(permissions, many=True).data
        return Response({**RESPONSE__200__SUCCESS,KEY.SUCCESS:detail}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'],url_path='edit')
    def edit(self,request):
        serializer = ResourceGroupAuthSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({**RESPONSE__200__SUCCESS}, status=status.HTTP_200_OK)
        return Response({**RESPONSE__400__FAILED, KEY.ERROR: serializer.errors}, status=status.HTTP_400_BAD_REQUEST)