from django.db import models
from resource.models import ResourceGroup

class SSHCommandFilter(models.Model):
    """SSH命令过滤规则表"""
    class Meta:
        db_table = 'ssh_command_filter'
    id = models.AutoField(primary_key=True)
    group = models.ForeignKey(ResourceGroup, on_delete=models.CASCADE, related_name='ssh_command_filters')
    pattern = models.CharField(max_length=255, help_text='命令模式')
    type = models.CharField(max_length=10, choices=[('exact', '精确匹配'), ('prefix', '前缀匹配'), ('regex', '正则匹配')], default='exact', help_text='匹配类型')
    priority = models.IntegerField(default=0, help_text='优先级（数值越大优先级越高）')
    description = models.TextField(null=True, blank=True, help_text='规则描述')
    create_date = models.DateTimeField(auto_now_add=True)
    update_date = models.DateTimeField(auto_now=True)
