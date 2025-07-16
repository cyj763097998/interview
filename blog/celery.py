# celery.py
from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# 设置 Django 的环境变量
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'interview.settings')

app = Celery('interview')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()