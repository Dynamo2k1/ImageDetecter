from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "forensic_worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.workers.tasks", "app.workers.scan_tasks"]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
)

# Optional: Add task routes
celery_app.conf.task_routes = {
    "app.workers.tasks.process_url_job": {"queue": "url_jobs"},
    "app.workers.tasks.process_upload_job": {"queue": "upload_jobs"},
    "app.workers.tasks.generate_pdf_report": {"queue": "reports"},
}