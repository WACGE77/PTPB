import os
from celery import Celery

# 设置 Django 环境变量
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'BackEnd.settings')

# 创建 Celery 应用
app = Celery('BackEnd')

# 从 Django 设置中加载 Celery 配置
app.config_from_object('django.conf:settings', namespace='CELERY')

# 使用 django_celery_beat 作为调度器
app.conf.beat_scheduler = 'django_celery_beat.schedulers:DatabaseScheduler'

# 自动发现所有 Django 应用中的 tasks.py
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
