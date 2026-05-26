from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "statusforge",
    broker=f"{settings.redis_url}/0",
    backend=f"{settings.redis_url}/0",
    include=["app.tasks.health_check"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    beat_schedule={
        "run-all-checks": {
            "task": "app.tasks.health_check.run_all_checks",
            "schedule": 10.0,
        },
    },
)
