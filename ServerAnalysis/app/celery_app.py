"""
Celery application configuration and initialization.
"""
from celery import Celery
from app.config import settings

# Initialize Celery app
celery_app = Celery('ServerAnalysis')

# Load configuration from settings
celery_app.conf.broker_url = settings.broker_url
celery_app.conf.result_backend = settings.result_backend

# Task routing
celery_app.conf.task_routes = settings.task_routes

# Queue configuration
celery_app.conf.task_default_queue = settings.task_default_queue
celery_app.conf.task_create_missing_queues = settings.task_create_missing_queues

# Result configuration
celery_app.conf.task_ignore_result = settings.task_ignore_result
celery_app.conf.task_store_eager_result = settings.task_store_eager_result

# Retry configuration
celery_app.conf.task_acks_late = settings.task_acks_late

# Logging
celery_app.conf.worker_hijack_root_logger = settings.worker_hijack_root_logger
celery_app.conf.worker_log_format = settings.worker_log_format
celery_app.conf.worker_task_log_format = settings.worker_task_log_format

# Autodiscover tasks from the tasks module
celery_app.autodiscover_tasks(['app.core.tasks'])

# Set up schedule for Celery beat
celery_app.conf.beat_schedule = settings.beat_schedule