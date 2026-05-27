import asyncio
import json
import logging
import uuid
from datetime import datetime

from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


def _run(coro):
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            raise RuntimeError
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


@celery_app.task(name="app.tasks.health_check.run_all_checks")
def run_all_checks():
    _run(_async_run_all_checks())


async def _async_run_all_checks():
    from sqlalchemy import select

    from app.core.database import async_session_factory
    from app.services.models import MonitoredService

    async with async_session_factory() as db:
        result = await db.execute(select(MonitoredService).where(MonitoredService.is_active == True))
        service_ids = [str(svc.id) for svc in result.scalars().all()]

    for sid in service_ids:
        check_service.delay(sid)


@celery_app.task(name="app.tasks.health_check.check_service")
def check_service(service_id: str, force: bool = False):
    _run(_async_check_service(uuid.UUID(service_id), force=force))


async def _async_check_service(service_id: uuid.UUID, force: bool = False):
    from sqlalchemy import select

    from app.core.database import async_session_factory
    from app.core.redis import get_pubsub_redis
    from app.incidents.models import IncidentSeverity
    from app.incidents.service import (
        create_incident,
        get_open_incident_for_service,
        resolve_incident,
    )
    from app.monitoring.models import HealthCheck
    from app.monitoring.probe import probe_http
    from app.notifications.models import NotificationSeverity
    from app.notifications.service import create_notifications_for_incident
    from app.services.models import MonitoredService, ServiceStatus

    async with async_session_factory() as db:
        result = await db.execute(select(MonitoredService).where(MonitoredService.id == service_id))
        svc = result.scalar_one_or_none()
        if not svc:
            return

        # Respect per-service check interval (skipped when force=True)
        if not force and svc.last_checked_at:
            elapsed = (datetime.utcnow() - svc.last_checked_at.replace(tzinfo=None)).total_seconds()
            if elapsed < svc.check_interval - 5:
                return

        probe = await probe_http(svc.url, svc.timeout)
        db.add(HealthCheck(
            service_id=service_id,
            status=probe["status"],
            latency_ms=probe["latency_ms"],
            status_code=probe["status_code"],
            error=probe["error"],
        ))

        prev_status = svc.status
        incident_created = None

        if probe["status"] == "DOWN":
            svc.consecutive_failures += 1
            if svc.consecutive_failures >= 2:
                svc.status = ServiceStatus.DOWN
                open_inc = await get_open_incident_for_service(db, service_id)
                if not open_inc:
                    incident = await create_incident(db, service_id, f"{svc.name} is DOWN", IncidentSeverity.CRITICAL)
                    await create_notifications_for_incident(db, incident.id, f"{svc.name} is DOWN", NotificationSeverity.CRITICAL)
                    incident_created = incident
        elif probe["status"] == "DEGRADED":
            svc.consecutive_failures = 0
            svc.status = ServiceStatus.DEGRADED
        else:
            svc.consecutive_failures = 0
            svc.status = ServiceStatus.UP
            if prev_status == ServiceStatus.DOWN:
                open_inc = await get_open_incident_for_service(db, service_id)
                if open_inc:
                    await resolve_incident(db, open_inc.id)

        svc.last_checked_at = datetime.utcnow()
        await db.commit()

    redis = get_pubsub_redis()
    msg = json.dumps({
        "type": "service_update",
        "service_id": str(service_id),
        "status": probe["status"],
        "latency_ms": probe["latency_ms"],
        "checked_at": datetime.utcnow().isoformat(),
    })
    await redis.publish("ws:global", msg)
    await redis.publish(f"ws:service:{service_id}", msg)

    if incident_created:
        await redis.publish("ws:global", json.dumps({
            "type": "incident_created",
            "incident_id": str(incident_created.id),
            "service_id": str(service_id),
            "severity": incident_created.severity,
            "title": incident_created.title,
        }))
