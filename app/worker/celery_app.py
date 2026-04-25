"""
Medix AI — Celery Worker
Tareas asíncronas y programadas:
- Reset de contadores de rate limit a medianoche HN (UTC-6)
- Procesamiento de scans en background (para plan Free con latencia aceptable)
- Alertas de suscripciones próximas a vencer
"""
from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

celery_app = Celery(
    "medix_worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.worker.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="America/Tegucigalpa",
    enable_utc=True,
    # ── Tareas programadas ───────────────────────────────────
    beat_schedule={
        # Reset contadores a medianoche hora de Honduras
        "reset-rate-limits-midnight": {
            "task": "app.worker.tasks.reset_daily_rate_limits",
            "schedule": crontab(hour=0, minute=0),
        },
        # Reporte diario de uso (para analytics)
        "daily-usage-report": {
            "task": "app.worker.tasks.generate_daily_report",
            "schedule": crontab(hour=6, minute=0),
        },
    },
)

# Agregar tarea de snapshot analítico a las tareas programadas
celery_app.conf.beat_schedule["daily-analytics-snapshot"] = {
    "task": "app.worker.tasks.generate_daily_analytics_snapshot",
    "schedule": crontab(hour=0, minute=5),  # 5 min después del reset de rate limits
}
