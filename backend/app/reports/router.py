from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.core.database import get_db
from app.incidents.models import Incident, IncidentStatus
from app.monitoring.models import HealthCheck
from app.services.models import MonitoredService

router = APIRouter(prefix="/reports", tags=["reports"])


class ServiceSLAReport(BaseModel):
    service_id: str
    service_name: str
    url: str
    uptime_percent: float | None
    avg_latency_ms: float | None
    total_checks: int
    incident_count: int
    total_downtime_minutes: int


@router.get("/sla", response_model=list[ServiceSLAReport])
async def get_sla_report(
    days: int = Query(default=30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    cutoff = datetime.utcnow() - timedelta(days=days)

    services_result = await db.execute(select(MonitoredService))
    services = list(services_result.scalars().all())

    report = []
    for svc in services:
        checks_result = await db.execute(
            select(HealthCheck).where(
                HealthCheck.service_id == svc.id,
                HealthCheck.checked_at >= cutoff,
            )
        )
        checks = list(checks_result.scalars().all())

        total = len(checks)
        up_count = sum(1 for c in checks if c.status == "UP")
        latencies = [c.latency_ms for c in checks if c.latency_ms is not None]

        uptime = round(up_count / total * 100, 2) if total > 0 else None
        avg_latency = round(sum(latencies) / len(latencies), 1) if latencies else None

        incidents_result = await db.execute(
            select(Incident).where(
                Incident.service_id == svc.id,
                Incident.started_at >= cutoff,
            )
        )
        incidents = list(incidents_result.scalars().all())

        downtime_minutes = 0
        now = datetime.utcnow()
        for inc in incidents:
            end = inc.resolved_at.replace(tzinfo=None) if inc.resolved_at else now
            start = inc.started_at.replace(tzinfo=None)
            downtime_minutes += max(0, int((end - start).total_seconds() / 60))

        report.append(ServiceSLAReport(
            service_id=str(svc.id),
            service_name=svc.name,
            url=svc.url,
            uptime_percent=uptime,
            avg_latency_ms=avg_latency,
            total_checks=total,
            incident_count=len(incidents),
            total_downtime_minutes=downtime_minutes,
        ))

    return report
