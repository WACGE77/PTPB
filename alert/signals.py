import logging
import json
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django_celery_beat.models import PeriodicTask, IntervalSchedule

from .models import ProbeRule

logger = logging.getLogger(__name__)


def _get_or_create_schedule(interval_seconds: int) -> IntervalSchedule:
    """
    获取或创建时间间隔调度器
    
    Args:
        interval_seconds: 间隔秒数
        
    Returns:
        IntervalSchedule 对象
    """
    schedule, created = IntervalSchedule.objects.get_or_create(
        every=interval_seconds,
        period=IntervalSchedule.SECONDS,
    )
    if created:
        logger.info(f'Created new interval schedule: {interval_seconds} seconds')
    return schedule


def _create_or_update_periodic_task(rule: ProbeRule):
    """
    创建或更新探针规则的定时任务
    
    Args:
        rule: 探针规则对象
    """
    task_name = f'probe_rule_{rule.id}'
    
    # 获取或创建调度器
    schedule = _get_or_create_schedule(rule.detect_interval)
    
    # 任务参数
    task_kwargs = {'rule_id': rule.id}
    
    try:
        # 尝试获取现有任务
        task = PeriodicTask.objects.get(name=task_name)
        
        # 更新任务配置
        task.interval = schedule
        task.task = 'alert.tasks.execute_probe_rule'
        task.kwargs = json.dumps(task_kwargs)
        task.enabled = rule.is_enabled
        task.save()
        
        logger.info(f'Updated periodic task for rule {rule.name}: enabled={rule.is_enabled}')
        
    except PeriodicTask.DoesNotExist:
        # 创建新任务
        PeriodicTask.objects.create(
            name=task_name,
            task='alert.tasks.execute_probe_rule',
            interval=schedule,
            kwargs=json.dumps(task_kwargs),
            enabled=rule.is_enabled,
        )
        logger.info(f'Created new periodic task for rule {rule.name}')


def _delete_periodic_task(rule: ProbeRule):
    """
    删除探针规则的定时任务
    
    Args:
        rule: 探针规则对象
    """
    task_name = f'probe_rule_{rule.id}'
    try:
        task = PeriodicTask.objects.get(name=task_name)
        task.delete()
        logger.info(f'Deleted periodic task for rule {rule.name}')
    except PeriodicTask.DoesNotExist:
        logger.warning(f'Periodic task not found for rule {rule.name}')


@receiver(post_save, sender=ProbeRule)
def probe_rule_post_save(sender, instance, created, **kwargs):
    """
    探针规则保存信号处理：创建或更新定时任务
    """
    # 检查 update_fields，只在关键字段变化时才更新
    update_fields = kwargs.get('update_fields')
    
    # 如果没有指定 update_fields，或者包含关键字段，才更新定时任务
    if update_fields is None or any(field in update_fields for field in ['is_enabled', 'detect_interval', 'name']):
        logger.info(f'Probe rule {instance.name} saved, updating periodic task')
        _create_or_update_periodic_task(instance)


@receiver(post_delete, sender=ProbeRule)
def probe_rule_post_delete(sender, instance, **kwargs):
    """
    探针规则删除信号处理：删除定时任务
    """
    logger.info(f'Probe rule {instance.name} deleted, removing periodic task')
    _delete_periodic_task(instance)
