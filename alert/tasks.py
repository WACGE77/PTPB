import logging
from datetime import datetime
from celery import shared_task
from django.utils import timezone

from .models import ProbeRule, ProbeLog
from .services.probe import ProbeService
from .services.alert import AlertService

logger = logging.getLogger(__name__)


@shared_task
def execute_probe_rule(rule_id: int):
    """
    执行探针规则任务
    
    Args:
        rule_id: 探针规则ID
    """
    try:
        rule = ProbeRule.objects.get(id=rule_id)
        
        if not rule.is_enabled:
            logger.info(f'Rule {rule_id} is disabled, skipping')
            return
        
        logger.info(f'Executing probe rule: {rule.name}')
        
        # 执行探测
        status = 'down'
        latency = None
        message = ''
        
        if rule.target_type == 'host':
            # 主机存活探测
            success, latency, message = ProbeService.ping_host(rule.target)
            status = 'up' if success else 'down'
        elif rule.target_type == 'port':
            # 端口探测
            try:
                host, port = rule.target.split(':')
                port = int(port)
                success, latency, message = ProbeService.tcp_port_check(host, port)
                status = 'up' if success else 'down'
            except ValueError:
                message = 'Invalid target format, should be host:port'
                status = 'down'
        
        # 更新规则状态
        now = timezone.now()
        rule.last_check_at = now
        
        if status == 'down':
            rule.consecutive_fail += 1
            logger.warning(f'Rule {rule.name} failed, consecutive fails: {rule.consecutive_fail}')

            # 检查是否需要告警（只要达到阈值就尝试触发，内部会检查间隔）
            if rule.consecutive_fail >= rule.fail_threshold:
                logger.info(f'Triggering alert for rule {rule.name}')
                alert_sent = _trigger_alert(rule, 'down', status, latency, message)
                if rule.last_status != 'down':
                    rule.last_status = 'down'
        else:
            # 探测成功
            if rule.last_status == 'down':
                # 从异常恢复
                logger.info(f'Rule {rule.name} recovered')
                alert_sent = _trigger_alert(rule, 'up', status, latency, message)
            
            rule.consecutive_fail = 0
            rule.last_status = 'up'
        
        # 只更新必要的字段，避免触发信号
        rule.save(update_fields=['last_check_at', 'consecutive_fail', 'last_status'])
        
    except ProbeRule.DoesNotExist:
        logger.error(f'Rule {rule_id} not found')
    except Exception as e:
        logger.error(f'Error executing probe rule {rule_id}: {e}', exc_info=True)


def _trigger_alert(rule: ProbeRule, status: str, probe_status: str, latency: float | None, message: str) -> bool:
    """
    触发告警，发送成功后记录探测日志
    
    Args:
        rule: 探针规则对象
        status: 告警状态（'up' 或 'down'）
        probe_status: 探测状态
        latency: 探测延迟
        message: 探测消息
    
    Returns:
        bool: 是否成功发送告警
    """
    try:
        if not rule.alert_method or not rule.alert_template:
            logger.info(f'No alert method or template configured for rule {rule.name}')
            return False
        
        # 检查告警间隔（每个探针规则独立设置）
        now = timezone.now()
        if rule.last_alert_sent_at:
            interval_seconds = (now - rule.last_alert_sent_at).total_seconds()
            if interval_seconds < rule.alert_interval:
                logger.info(f'Skipping alert for {rule.name}, still in interval. '
                           f'Last sent: {interval_seconds:.0f}s ago, '
                           f'interval: {rule.alert_interval}s')
                return False
        
        # 准备上下文
        context = {
            'rule_name': rule.name,
            'target_type': rule.get_target_type_display(),
            'target': rule.target,
            'fail_count': rule.consecutive_fail,
            'last_check_time': rule.last_check_at.strftime('%Y-%m-%d %H:%M:%S') if rule.last_check_at else '',
            'status': '异常' if status == 'down' else '恢复'
        }
        
        # 发送告警
        success = AlertService.send_alert(
            rule.alert_method,
            rule.alert_template,
            context
        )
        
        if success:
            logger.info(f'Alert sent successfully for rule {rule.name}')
            # 更新上次发送时间
            rule.last_alert_sent_at = now
            rule.save(update_fields=['last_alert_sent_at'])
            
            # 发送成功后记录探测日志
            ProbeLog.objects.create(
                rule=rule,
                status=probe_status,
                latency=latency,
                message=message
            )
            logger.info(f'Probe log recorded for rule {rule.name} (alert sent)')
        else:
            logger.error(f'Failed to send alert for rule {rule.name}')
            
        return success
            
    except Exception as e:
        logger.error(f'Error triggering alert for rule {rule.name}: {e}', exc_info=True)
        return False


@shared_task
def schedule_all_probes():
    """
    调度所有启用的探针规则
    """
    try:
        rules = ProbeRule.objects.filter(is_enabled=True)
        logger.info(f'Scheduling {rules.count()} probe rules')
        
        for rule in rules:
            # 为每个规则创建定时任务
            # 注意：这里需要使用 Celery Beat 来管理定时任务
            execute_probe_rule.apply_async(args=[rule.id])
            
    except Exception as e:
        logger.error(f'Error scheduling probes: {e}', exc_info=True)
