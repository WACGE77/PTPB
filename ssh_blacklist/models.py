from django.db import models


class DangerCommandRule(models.Model):
    """危险命令告警规则"""
    class Meta:
        db_table = 'ssh_blacklist_rule'
        verbose_name = '危险命令告警规则'
        verbose_name_plural = '危险命令告警规则'

    TYPE_CHOICES = [
        ('exact', '精确匹配'),
        ('prefix', '前缀匹配'),
        ('regex', '正则匹配'),
    ]

    group = models.ForeignKey('resource.ResourceGroup', on_delete=models.CASCADE, verbose_name='系统组', related_name='danger_command_rules')
    pattern = models.CharField(verbose_name='匹配模式', max_length=255)
    type = models.CharField(verbose_name='匹配类型', max_length=20, choices=TYPE_CHOICES, default='exact')
    priority = models.IntegerField(verbose_name='优先级', default=0)
    is_active = models.BooleanField(verbose_name='是否启用', default=True)
    description = models.TextField(verbose_name='描述', blank=True, null=True)
    created_at = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name='更新时间', auto_now=True)

    def __str__(self):
        return f'[{self.group.name}] {self.get_type_display()}: {self.pattern}'
