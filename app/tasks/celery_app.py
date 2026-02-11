from celery import Celery
from app.config import settings

# Create Celery instance
celery_app = Celery(
    "careops",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.tasks.email_tasks",
        "app.tasks.sms_tasks",
        "app.tasks.booking_tasks",
        "app.tasks.form_tasks",
        "app.tasks.inventory_tasks",
        "app.tasks.automation_tasks"
    ]
)

# Configure Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_disable_rate_limits=True,
    result_expires=3600,  # 1 hour
)

# Task routes
celery_app.conf.task_routes = {
    'app.tasks.email_tasks.*': {'queue': 'emails'},
    'app.tasks.sms_tasks.*': {'queue': 'sms'},
    'app.tasks.booking_tasks.*': {'queue': 'bookings'},
    'app.tasks.form_tasks.*': {'queue': 'forms'},
    'app.tasks.inventory_tasks.*': {'queue': 'inventory'},
    'app.tasks.automation_tasks.*': {'queue': 'automation'},
}

# Beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    'check-overdue-forms': {
        'task': 'app.tasks.form_tasks.check_overdue_forms',
        'schedule': 60.0 * 60,  # Every hour
    },
    'check-low-inventory': {
        'task': 'app.tasks.inventory_tasks.check_low_inventory',
        'schedule': 60.0 * 60 * 6,  # Every 6 hours
    },
    'send-daily-reminders': {
        'task': 'app.tasks.booking_tasks.send_daily_reminders',
        'schedule': 60.0 * 60 * 24,  # Daily at midnight
    },
}