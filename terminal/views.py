
from rest_framework.response import Response
from rest_framework.views import APIView

from perm.authentication import ResourcePermission, TokenPermission
from perm.models import BaseAuth


# Create your views here.
class Test(APIView):
    permission_classes = [TokenPermission,ResourcePermission]
    permission_code = 'resource.self.read'
    def post(self, request):
        resource = request.data.get('resource_id')
        return Response({'resource': resource})