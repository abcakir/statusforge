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
        get_open_ssl_incident_for_service,
        resolve_incident,
    )
    from app.monitoring.models import HealthCheck
    from app.monitoring.probe import probe_http
    from app.monitoring.ssl import check_ssl_certificate
    from app.notifications.email import send_incident_email
    from app.notifications.models import NotificationSeverity
    from app.notifications.service import create_notifications_for_incident
    from app.users.models import User
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

        # Immediate retry on failure to avoid false positives from transient errors
        if probe["status"] == "DOWN":
            logger.info("Service %s failed, retrying in 5s…", svc.name)
            await asyncio.sleep(5)
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
        incident_resolved = None
        incident_emails: tuple | None = None
        resolved_emails: tuple | None = None

        severity = IncidentSeverity(svc.incident_severity)
        notif_severity = NotificationSeverity(svc.incident_severity)

        if probe["latency_ms"] and probe["latency_ms"] > svc.latency_threshold_ms and probe["status"] == "UP":
            probe["status"] = "DEGRADED"

        if probe["status"] == "DOWN":
            svc.consecutive_failures += 1
            if svc.consecutive_failures >= svc.failure_threshold:
                svc.status = ServiceStatus.DOWN
                open_inc = await get_open_incident_for_service(db, service_id)
                if not open_inc:
                    incident = await create_incident(db, service_id, f"{svc.name} is DOWN", severity)
                    await create_notifications_for_incident(db, incident.id, f"{svc.name} is DOWN", notif_severity)
                    email_result = await db.execute(
                        select(User).where(User.role.in_(["ADMIN", "OPERATOR"]), User.is_active == True)
                    )
                    emails = [u.email for u in email_result.scalars().all() if u.email]
                    incident_created = incident
                    incident_emails = (emails, svc.name, "DOWN", incident.title)
        elif probe["status"] == "DEGRADED":
            svc.consecutive_failures = 0
            svc.status = ServiceStatus.DEGRADED
        else:
            svc.consecutive_failures = 0
            svc.status = ServiceStatus.UP
            if prev_status == ServiceStatus.DOWN:
                open_inc = await get_open_incident_for_service(db, service_id)
                if open_inc:
                    incident_resolved = await resolve_incident(db, open_inc.id)
                    email_result = await db.execute(
                        select(User).where(User.role.in_(["ADMIN", "OPERATOR"]), User.is_active == True)
                    )
                    emails = [u.email for u in email_result.scalars().all() if u.email]
                    resolved_emails = (emails, svc.name, "UP", f"{svc.name} is back UP")

        svc.last_checked_at = datetime.utcnow()
        await db.commit()

    # SSL check — once per hour for HTTPS services
    ssl_incident_created = None
    ssl_incident_emails: tuple | None = None
    if svc.url.startswith("https://"):
        needs_ssl_check = (
            force or
            not svc.ssl_checked_at or
            (datetime.utcnow() - svc.ssl_checked_at.replace(tzinfo=None)).total_seconds() > 3600
        )
        if needs_ssl_check:
            ssl_result = await check_ssl_certificate(svc.url, svc.timeout)
            if ssl_result["checked"]:
                async with async_session_factory() as db:
                    result = await db.execute(select(MonitoredService).where(MonitoredService.id == service_id))
                    svc = result.scalar_one_or_none()
                    svc.ssl_expires_at = ssl_result.get("expires_at")
                    svc.ssl_checked_at = datetime.utcnow()

                    days = ssl_result.get("days_remaining")
                    if not ssl_result["valid"] or (days is not None and days <= 0):
                        ssl_sev = IncidentSeverity.CRITICAL
                        ssl_title = f"SSL certificate for {svc.name} has expired"
                    elif days is not None and days <= 7:
                        ssl_sev = IncidentSeverity.CRITICAL
                        ssl_title = f"SSL certificate for {svc.name} expires in {days} days"
                    elif days is not None and days <= 30:
                        ssl_sev = IncidentSeverity.HIGH
                        ssl_title = f"SSL certificate for {svc.name} expires in {days} days"
                    else:
                        ssl_sev = None
                        ssl_title = None

                    if ssl_sev and ssl_title:
                        open_ssl = await get_open_ssl_incident_for_service(db, service_id)
                        if not open_ssl:
                            notif_sev = NotificationSeverity(ssl_sev.value)
                            ssl_inc = await create_incident(db, service_id, ssl_title, ssl_sev)
                            await create_notifications_for_incident(db, ssl_inc.id, ssl_title, notif_sev)
                            email_result = await db.execute(
                                select(User).where(User.role.in_(["ADMIN", "OPERATOR"]), User.is_active == True)
                            )
                            emails = [u.email for u in email_result.scalars().all() if u.email]
                            ssl_incident_created = ssl_inc
                            ssl_incident_emails = (emails, svc.name, "DOWN", ssl_title)

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

    if incident_resolved:
        await redis.publish("ws:global", json.dumps({
            "type": "incident_updated",
            "incident_id": str(incident_resolved.id),
            "status": "RESOLVED",
        }))

    if incident_emails:
        await send_incident_email(*incident_emails)
    if resolved_emails:
        await send_incident_email(*resolved_emails)

    if ssl_incident_created:
        await redis.publish("ws:global", json.dumps({
            "type": "incident_created",
            "incident_id": str(ssl_incident_created.id),
            "service_id": str(service_id),
            "severity": ssl_incident_created.severity,
            "title": ssl_incident_created.title,
        }))
    if ssl_incident_emails:
        await send_incident_email(*ssl_incident_emails)
