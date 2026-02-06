from Utils.Const import METHODS, PERMISSIONS
from Utils.modelViewSet import RModelViewSet
from audit.filter import LoginLogFilter, OperationLogFilter
from audit.models import LoginLog, OperationLog, SessionLog
from audit.serialization import LoginLogSerializer, OperationLogSerializer, SessionLogSerializer
from perm.authentication import AuditPermission
# Create your views here

class _AuditViewSet(RModelViewSet):
    permission_classes = [AuditPermission]
    def search(self,request):
        read_self = self.request.GET.get('self')
        query = self.model.objects.all()
        if read_self:
            query = query.filter(user=request.user)
        return query

class LoginLogViewSet(_AuditViewSet):
    model = LoginLog
    serializer_class = LoginLogSerializer
    filterset_class = LoginLogFilter
    permission_mapping = {
        METHODS.READ_ALL : PERMISSIONS.AUDIT.LOGIN.READ,
        METHODS.READ_SELF : PERMISSIONS.USER.PROFILE.READ
    }


class OperationLogViewSet(_AuditViewSet):
    model = OperationLog
    serializer_class = OperationLogSerializer
    filterset_class = OperationLogFilter
    permission_mapping = {
        METHODS.READ_ALL : PERMISSIONS.AUDIT.OPERATION.READ,
        METHODS.READ_SELF : PERMISSIONS.USER.PROFILE.READ
    }

class SessionLogViewSet(_AuditViewSet):
    model = SessionLog
    serializer_class = SessionLogSerializer
    filterset_class = LoginLogFilter
    permission_mapping = {
        METHODS.READ_ALL: PERMISSIONS.AUDIT.SESSION.READ,
        METHODS.READ_SELF: PERMISSIONS.USER.PROFILE.READ
    }