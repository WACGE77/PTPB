from django.db import models


class GlobalSMTPConfig(models.Model):
    """全局SMTP服务器配置"""
    class Meta:
        db_table = 'global_smtp_config'
        verbose_name = '全局SMTP配置'
        verbose_name_plural = '全局SMTP配置'

    smtp_host = models.CharField(verbose_name='SMTP服务器', max_length=128, default='smtp.qq.com')
    smtp_port = models.IntegerField(verbose_name='SMTP端口', default=465)
    smtp_username = models.CharField(verbose_name='SMTP用户名', max_length=128, blank=True, null=True)
    smtp_password = models.CharField(verbose_name='SMTP密码', max_length=256, blank=True, null=True)
    smtp_ssl = models.BooleanField(verbose_name='启用SSL', default=True)
    is_active = models.BooleanField(verbose_name='是否启用', default=True)
    created_at = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name='更新时间', auto_now=True)

    def __str__(self):
        return f'{self.smtp_host}:{self.smtp_port}'


class AlertMethod(models.Model):
    """告警方式"""
    class Meta:
        db_table = 'alert_method'
        verbose_name = '告警方式'
        verbose_name_plural = '告警方式'

    TYPE_CHOICES = [
        ('email', '邮箱告警'),
    ]

    name = models.CharField(verbose_name='告警名称', max_length=64)
    type = models.CharField(verbose_name='告警类型', max_length=20, choices=TYPE_CHOICES, default='email')
    to_list = models.JSONField(verbose_name='收件人列表', default=list, help_text='邮箱地址列表')
    created_at = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name='更新时间', auto_now=True)

    def __str__(self):
        return self.name


class AlertTemplate(models.Model):
    """告警内容模板"""
    class Meta:
        db_table = 'alert_template'
        verbose_name = '告警模板'
        verbose_name_plural = '告警模板'

    name = models.CharField(verbose_name='模板名称', max_length=128)
    title = models.CharField(verbose_name='告警标题', max_length=256)
    content = models.TextField(verbose_name='告警内容模板')
    created_at = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name='更新时间', auto_now=True)

    def __str__(self):
        return self.name


class ProbeRule(models.Model):
    """探针规则"""
    class Meta:
        db_table = 'probe_rule'
        verbose_name = '探针规则'
        verbose_name_plural = '探针规则'

    TARGET_TYPE_CHOICES = [
        ('host', '主机'),
        ('port', '端口'),
    ]

    STATUS_CHOICES = [
        ('up', '正常'),
        ('down', '异常'),
    ]

    name = models.CharField(verbose_name='规则名称', max_length=128)
    target_type = models.CharField(verbose_name='目标类型', max_length=10, choices=TARGET_TYPE_CHOICES)
    target = models.CharField(verbose_name='目标 IP/IP:端口', max_length=256)
    detect_interval = models.IntegerField(verbose_name='探测间隔(秒)', default=60)
    fail_threshold = models.IntegerField(verbose_name='连续失败次数告警', default=3)
    alert_interval = models.IntegerField(verbose_name='告警间隔(秒)', default=300, help_text='两次告警之间的最小间隔时间')
    is_enabled = models.BooleanField(verbose_name='是否启用', default=True)

    alert_method = models.ForeignKey(AlertMethod, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='告警方式')
    alert_template = models.ForeignKey(AlertTemplate, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='告警模板')

    last_status = models.CharField(verbose_name='最后状态', max_length=10, choices=STATUS_CHOICES, null=True, blank=True)
    last_check_at = models.DateTimeField(verbose_name='最后探测时间', null=True, blank=True)
    last_alert_sent_at = models.DateTimeField(verbose_name='上次告警发送时间', null=True, blank=True)
    consecutive_fail = models.IntegerField(verbose_name='连续失败次数', default=0)

    created_at = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name='更新时间', auto_now=True)

    def __str__(self):
        return self.name


class ProbeLog(models.Model):
    """探测日志"""
    class Meta:
        db_table = 'probe_log'
        verbose_name = '探测日志'
        verbose_name_plural = '探测日志'
        ordering = ['-created_at']

    STATUS_CHOICES = [
        ('up', '正常'),
        ('down', '异常'),
    ]

    rule = models.ForeignKey(ProbeRule, on_delete=models.CASCADE, verbose_name='探针规则', related_name='logs')
    status = models.CharField(verbose_name='状态', max_length=10, choices=STATUS_CHOICES)
    latency = models.FloatField(verbose_name='耗时(ms)', null=True, blank=True)
    message = models.TextField(verbose_name='消息', default='')
    created_at = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)

    def __str__(self):
        return f'{self.rule.name} - {self.status}'
