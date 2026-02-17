import django_filters

from audit.models import LoginLog, OperationLog, SessionLog


class LoginLogFilter(django_filters.rest_framework.FilterSet):
    user = django_filters.CharFilter(field_name='user__name', lookup_expr='icontains')
    ip = django_filters.CharFilter(field_name='ip', lookup_expr='icontains')
    start_time = django_filters.DateTimeFilter(field_name='date', lookup_expr='gte')
    end_time = django_filters.DateTimeFilter(field_name='date', lookup_expr='lte')
    class Meta:
        model = LoginLog
        fields = ['user', 'ip', 'start_time']
class OperationLogFilter(LoginLogFilter):
    operation = django_filters.CharFilter(field_name='operation', lookup_expr='icontains')
    class Meta:
        model = OperationLog
        fields = ['user', 'ip', 'start_time', 'end_time', 'operation']
class SessionLogFilter(django_filters.rest_framework.FilterSet):
    resource = django_filters.CharFilter(field_name='resource__name', lookup_expr='icontains')
    user = django_filters.CharFilter(field_name='user__name', lookup_expr='icontains')
    ip = django_filters.CharFilter(field_name='ip', lookup_expr='icontains')
    start_time = django_filters.DateTimeFilter(field_name='start_time', lookup_expr='gte')
    end_time = django_filters.DateTimeFilter(field_name='start_time', lookup_expr='lte')
    class Meta:
        model = SessionLog
        fields = ['resource', 'user', 'ip', 'start_time']