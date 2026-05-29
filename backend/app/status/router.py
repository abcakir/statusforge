from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.incidents.models import Incident, IncidentStatus
from app.services.models import MonitoredService, ServiceStatus

router = APIRouter(prefix="/status", tags=["status"])


class ServiceStatusItem(BaseModel):
    name: str
    status: str
    last_checked_at: datetime | None


class ActiveIncidentItem(BaseModel):
    title: str
    severity: str
    status: str
    started_at: datetime


class SystemStatus(BaseModel):
    overall: str  # "operational" | "partial_outage" | "major_outage"
    services: list[ServiceStatusItem]
    active_incidents: list[ActiveIncidentItem]
    checked_at: datetime


@router.get("", response_model=SystemStatus)
async def get_status(db: AsyncSession = Depends(get_db)):
    services_result = await db.execute(
        select(MonitoredService).where(MonitoredService.is_active == True)
    )
    services = list(services_result.scalars().all())

    cutoff = datetime.utcnow() - timedelta(days=7)
    incidents_result = await db.execute(
        select(Incident).where(
            Incident.status != IncidentStatus.RESOLVED,
            Incident.started_at >= cutoff,
        )
    )
    active_incidents = list(incidents_result.scalars().all())

    down_count = sum(1 for s in services if s.status == ServiceStatus.DOWN)
    degraded_count = sum(1 for s in services if s.status == ServiceStatus.DEGRADED)

    if down_count > 0 and down_count == len(services):
        overall = "major_outage"
    elif down_count > 0 or degraded_count > 0:
        overall = "partial_outage"
    else:
        overall = "operational"

    return SystemStatus(
        overall=overall,
        services=[
            ServiceStatusItem(name=s.name, status=s.status, last_checked_at=s.last_checked_at)
            for s in services
        ],
        active_incidents=[
            ActiveIncidentItem(title=i.title, severity=i.severity, status=i.status, started_at=i.started_at)
            for i in active_incidents
        ],
        checked_at=datetime.utcnow(),
    )
