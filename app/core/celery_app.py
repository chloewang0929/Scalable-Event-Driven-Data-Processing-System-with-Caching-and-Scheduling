from celery import Celery
from app.core.config import settings
import os

os.environ.setdefault('FORKED_BY_MULTIPROCESSING', '1')

celery_app = Celery(
    "event_worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.workers.tasks", "app.workers.scheduler"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    beat_schedule={
        'aggregate-daily-transactions': {
            'task': 'app.workers.scheduler.aggregate_daily',
            'schedule': 60.0, # 配合 Demo，每 60 秒跑一次而不是一天跑一次
        },
    }
)
