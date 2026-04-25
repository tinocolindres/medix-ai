"""
Medix AI — Celery Tasks
"""
import asyncio
import structlog
from datetime import datetime, timezone
from sqlalchemy import update

from app.worker.celery_app import celery_app
from app.db.session import AsyncSessionLocal
from app.models.user import User

logger = structlog.get_logger()


def run_async(coro):
    """Helper para ejecutar coroutines desde Celery (sync context)."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(name="app.worker.tasks.reset_daily_rate_limits", bind=True, max_retries=3)
def reset_daily_rate_limits(self):
    """
    Resetea los contadores de chat y scan de todos los usuarios.
    Ejecutado a medianoche Honduras (UTC-6).
    """
    async def _reset():
        async with AsyncSessionLocal() as db:
            try:
                await db.execute(
                    update(User).values(
                        chat_count_today=0,
                        scan_count_today=0,
                        rate_limit_reset_at=datetime.now(timezone.utc),
                    )
                )
                await db.commit()
                logger.info("✅ Rate limits reseteados exitosamente")
                return {"status": "ok", "reset_at": datetime.now(timezone.utc).isoformat()}
            except Exception as e:
                await db.rollback()
                logger.error("❌ Error reseteando rate limits", error=str(e))
                raise

    try:
        return run_async(_reset())
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(name="app.worker.tasks.generate_daily_report")
def generate_daily_report():
    """
    Genera reporte diario de uso para analytics internos.
    Ejecutado a las 6:00 AM Honduras.
    """
    async def _report():
        async with AsyncSessionLocal() as db:
            from sqlalchemy import select, func
            from app.models.medical import ChatMessage, MedicalScan

            # Mensajes de ayer
            result = await db.execute(
                select(func.count(ChatMessage.id))
            )
            total_messages = result.scalar()

            result2 = await db.execute(
                select(func.count(MedicalScan.id)).where(MedicalScan.is_processed == True)
            )
            total_scans = result2.scalar()

            result3 = await db.execute(
                select(func.count(User.id)).where(User.is_active == True)
            )
            active_users = result3.scalar()

            logger.info(
                "📊 Reporte diario Medix AI",
                total_messages=total_messages,
                total_scans=total_scans,
                active_users=active_users,
                date=datetime.now(timezone.utc).date().isoformat(),
            )
            return {
                "date": datetime.now(timezone.utc).date().isoformat(),
                "total_messages": total_messages,
                "total_scans": total_scans,
                "active_users": active_users,
            }

    return run_async(_report())


@celery_app.task(name="app.worker.tasks.process_scan_background")
def process_scan_background(scan_id: str, image_url: str, scan_type: str, user_context: str = None):
    """
    Procesa un MedScan en background para usuarios Free (menor prioridad).
    Clinical: procesamiento síncrono (ya implementado en el endpoint).
    """
    async def _process():
        from app.services.vision import analyze_image_from_url
        from app.models.medical import MedicalScan
        from sqlalchemy import select

        async with AsyncSessionLocal() as db:
            result = await db.execute(select(MedicalScan).where(MedicalScan.id == scan_id))
            scan = result.scalar_one_or_none()
            if not scan:
                return {"error": "scan_not_found"}

            try:
                analysis = await analyze_image_from_url(image_url, scan_type, user_context)
                scan.ai_summary = analysis.get("summary")
                scan.ai_findings = analysis.get("findings")
                scan.ai_recommendations = analysis.get("recommendations")
                scan.urgency_level = analysis.get("urgency_level", "low")
                scan.confidence_score = analysis.get("confidence_score", 0.8)
                scan.is_processed = True
                scan.processing_time_ms = analysis.get("processing_time_ms")
                await db.commit()
                return {"status": "ok", "scan_id": scan_id}
            except Exception as e:
                scan.processing_error = str(e)
                await db.commit()
                return {"status": "error", "error": str(e)}

    return run_async(_process())


@celery_app.task(name="app.worker.tasks.generate_daily_analytics_snapshot")
def generate_daily_analytics_snapshot():
    """Genera snapshot de métricas de ayer. Ejecutado a medianoche."""
    async def _run():
        async with AsyncSessionLocal() as db:
            try:
                from app.services.analytics import generate_daily_snapshot
                snapshot = await generate_daily_snapshot(db)
                await db.commit()
                logger.info("📊 Snapshot diario generado", date=snapshot.date,
                            users=snapshot.active_users)
                return {"status": "ok", "date": snapshot.date}
            except Exception as e:
                await db.rollback()
                logger.error("Error generando snapshot", error=str(e))
                raise
    return run_async(_run())
