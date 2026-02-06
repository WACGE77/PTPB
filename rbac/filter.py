import django_filters

from rbac.models import User

class RoleFilter(django_filters.rest_framework.FilterSet):
    name = django_filters.CharFilter(field_name='name',lookup_expr='icontains')
    class Meta:
        model = User
        fields = ['name','email','phone_number','create_date']
class UserFilter(RoleFilter):
    name = django_filters.CharFilter(field_name='name',lookup_expr='icontains')
    email =django_filters.CharFilter(field_name='email',lookup_expr='icontains')
    phone_number = django_filters.CharFilter(field_name='phone_number',lookup_expr='icontains')
    start_time = django_filters.DateTimeFilter(field_name='create_date', lookup_expr='gte')
    end_time = django_filters.DateTimeFilter(field_name='create_date', lookup_expr='lte')
    class Meta:
        model = User
        fields = ['name','email','phone_number','create_date']

