import uuid
from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.incidents.models import Incident, IncidentStatus
from app.monitoring.models import CheckStatus, HealthCheck
from app.services.models import MonitoredService, ServiceStatus


async def get_overview(db: AsyncSession) -> dict:
    rows = await db.execute(select(MonitoredService.status, func.count()).group_by(MonitoredService.status))
    counts = {row[0]: row[1] for row in rows}

    open_inc = await db.execute(
        select(func.count()).select_from(Incident).where(Incident.status != IncidentStatus.RESOLVED)
    )

    total = sum(counts.values())
    return {
        "total_services": total,
        "up": counts.get(ServiceStatus.UP, 0),
        "down": counts.get(ServiceStatus.DOWN, 0),
        "degraded": counts.get(ServiceStatus.DEGRADED, 0),
        "open_incidents": open_inc.scalar(),
    }


async def get_latency_series(db: AsyncSession, service_id: uuid.UUID, hours: int = 24) -> list[dict]:
    since = datetime.utcnow() - timedelta(hours=hours)
    result = await db.execute(
        select(HealthCheck)
        .where(HealthCheck.service_id == service_id, HealthCheck.checked_at >= since)
        .order_by(HealthCheck.checked_at)
        .limit(500)
    )
    return [{"timestamp": c.checked_at.isoformat(), "latency_ms": c.latency_ms} for c in result.scalars()]


async def get_uptime(db: AsyncSession, service_id: uuid.UUID, days: int = 30) -> dict:
    since = datetime.utcnow() - timedelta(days=days)
    result = await db.execute(
        select(HealthCheck).where(HealthCheck.service_id == service_id, HealthCheck.checked_at >= since)
    )
    checks = result.scalars().all()
    if not checks:
        return {"uptime_percent": None, "total_checks": 0}
    up = sum(1 for c in checks if c.status == CheckStatus.UP)
    return {"uptime_percent": round(up / len(checks) * 100, 2), "total_checks": len(checks)}
