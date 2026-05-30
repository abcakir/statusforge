from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from prometheus_client import CollectorRegistry, Gauge, generate_latest, CONTENT_TYPE_LATEST
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.incidents.models import Incident, IncidentStatus
from app.monitoring.models import HealthCheck
from app.services.models import MonitoredService, ServiceStatus

router = APIRouter(tags=["prometheus"])


@router.get("/metrics", include_in_schema=False)
async def prometheus_metrics(db: AsyncSession = Depends(get_db)):
    registry = CollectorRegistry()

    # --- overview gauges ---
    status_rows = await db.execute(
        select(MonitoredService.status, func.count()).group_by(MonitoredService.status)
    )
    counts = {row[0]: row[1] for row in status_rows}
    total = sum(counts.values())

    open_inc_result = await db.execute(
        select(func.count()).select_from(Incident).where(Incident.status != IncidentStatus.RESOLVED)
    )

    Gauge("statusforge_services_total", "Total monitored services", registry=registry).set(total)
    Gauge("statusforge_services_up", "Services with UP status", registry=registry).set(counts.get(ServiceStatus.UP, 0))
    Gauge("statusforge_services_down", "Services with DOWN status", registry=registry).set(counts.get(ServiceStatus.DOWN, 0))
    Gauge("statusforge_services_degraded", "Services with DEGRADED status", registry=registry).set(counts.get(ServiceStatus.DEGRADED, 0))
    Gauge("statusforge_open_incidents_total", "Open incidents", registry=registry).set(open_inc_result.scalar() or 0)

    # --- per-service gauges ---
    services_result = await db.execute(select(MonitoredService).where(MonitoredService.is_active == True))
    services = list(services_result.scalars().all())

    latency_g = Gauge("statusforge_service_latency_ms", "Last HTTP check latency in ms", ["service"], registry=registry)
    uptime_g = Gauge("statusforge_service_uptime_percent", "30-day uptime percent", ["service"], registry=registry)
    ssl_g = Gauge("statusforge_service_ssl_days_remaining", "SSL certificate days remaining", ["service"], registry=registry)
    status_g = Gauge("statusforge_service_up", "1 if service is UP, 0 otherwise", ["service"], registry=registry)

    # Latest latency per service via subquery
    subq = (
        select(HealthCheck.service_id, func.max(HealthCheck.checked_at).label("max_at"))
        .group_by(HealthCheck.service_id)
        .subquery()
    )
    latest_checks_result = await db.execute(
        select(HealthCheck).join(
            subq,
            (HealthCheck.service_id == subq.c.service_id) &
            (HealthCheck.checked_at == subq.c.max_at),
        )
    )
    latest_by_service = {str(c.service_id): c for c in latest_checks_result.scalars().all()}

    # 30-day uptime per service
    since = datetime.utcnow() - timedelta(days=30)
    uptime_rows = await db.execute(
        select(HealthCheck.service_id, HealthCheck.status)
        .where(HealthCheck.checked_at >= since)
    )
    uptime_raw: dict[str, list[str]] = {}
    for row in uptime_rows:
        sid = str(row.service_id)
        uptime_raw.setdefault(sid, []).append(row.status)
    uptime_by_service = {
        sid: (len(statuses), sum(1 for s in statuses if s == "UP"))
        for sid, statuses in uptime_raw.items()
    }

    for svc in services:
        name = svc.name
        sid = str(svc.id)

        status_g.labels(service=name).set(1 if svc.status == ServiceStatus.UP else 0)

        check = latest_by_service.get(sid)
        if check and check.latency_ms is not None:
            latency_g.labels(service=name).set(check.latency_ms)

        if sid in uptime_by_service:
            total_c, up_c = uptime_by_service[sid]
            if total_c and up_c is not None:
                uptime_g.labels(service=name).set(round((up_c / total_c) * 100, 2))

        if svc.ssl_expires_at is not None:
            days = (svc.ssl_expires_at.replace(tzinfo=None) - datetime.utcnow()).days
            ssl_g.labels(service=name).set(days)

    return Response(generate_latest(registry), media_type=CONTENT_TYPE_LATEST)
