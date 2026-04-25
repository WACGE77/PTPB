import django_filters
from .models import ProbeRule, AlertMethod, AlertTemplate


class ProbeRuleFilter(django_filters.rest_framework.FilterSet):
    name = django_filters.CharFilter(field_name='name', lookup_expr='icontains')
    target = django_filters.CharFilter(field_name='target', lookup_expr='icontains')
    target_type = django_filters.CharFilter(field_name='target_type', lookup_expr='exact')
    is_enabled = django_filters.BooleanFilter(field_name='is_enabled', lookup_expr='exact')

    class Meta:
        model = ProbeRule
        fields = ['name', 'target', 'target_type', 'is_enabled']


class AlertMethodFilter(django_filters.rest_framework.FilterSet):
    name = django_filters.CharFilter(field_name='name', lookup_expr='icontains')
    type = django_filters.CharFilter(field_name='type', lookup_expr='exact')

    class Meta:
        model = AlertMethod
        fields = ['name', 'type']


class AlertTemplateFilter(django_filters.rest_framework.FilterSet):
    name = django_filters.CharFilter(field_name='name', lookup_expr='icontains')
    title = django_filters.CharFilter(field_name='title', lookup_expr='icontains')

    class Meta:
        model = AlertTemplate
        fields = ['name', 'title']
