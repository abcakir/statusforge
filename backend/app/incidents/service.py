import logging
import uuid
from datetime import datetime

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.incidents.models import Incident, IncidentEvent, IncidentEventType, IncidentSeverity, IncidentStatus

logger = logging.getLogger(__name__)


async def get_all_incidents(db: AsyncSession) -> list[Incident]:
    result = await db.execute(select(Incident).order_by(desc(Incident.created_at)))
    return list(result.scalars().all())


async def get_incident(db: AsyncSession, incident_id: uuid.UUID) -> Incident | None:
    result = await db.execute(select(Incident).where(Incident.id == incident_id))
    return result.scalar_one_or_none()


async def get_open_incident_for_service(db: AsyncSession, service_id: uuid.UUID) -> Incident | None:
    result = await db.execute(
        select(Incident).where(
            Incident.service_id == service_id,
            Incident.status != IncidentStatus.RESOLVED,
        )
    )
    return result.scalar_one_or_none()


async def create_incident(
    db: AsyncSession, service_id: uuid.UUID, title: str, severity: IncidentSeverity
) -> Incident:
    incident = Incident(service_id=service_id, title=title, severity=severity)
    db.add(incident)
    await db.flush()
    db.add(IncidentEvent(incident_id=incident.id, event_type=IncidentEventType.CREATED, message=title))
    await db.commit()
    await db.refresh(incident)
    logger.info("Created incident %s for service %s", incident.id, service_id)
    return incident


async def acknowledge_incident(db: AsyncSession, incident_id: uuid.UUID, user_id: uuid.UUID) -> Incident | None:
    incident = await get_incident(db, incident_id)
    if not incident:
        return None
    incident.status = IncidentStatus.ACKNOWLEDGED
    db.add(IncidentEvent(incident_id=incident_id, user_id=user_id, event_type=IncidentEventType.ACKNOWLEDGED))
    await db.commit()
    await db.refresh(incident)
    return incident


async def resolve_incident(db: AsyncSession, incident_id: uuid.UUID, user_id: uuid.UUID | None = None) -> Incident | None:
    incident = await get_incident(db, incident_id)
    if not incident:
        return None
    incident.status = IncidentStatus.RESOLVED
    incident.resolved_at = datetime.utcnow()
    db.add(IncidentEvent(incident_id=incident_id, user_id=user_id, event_type=IncidentEventType.RESOLVED))
    await db.commit()
    await db.refresh(incident)
    return incident


async def get_incident_events(db: AsyncSession, incident_id: uuid.UUID) -> list[IncidentEvent]:
    result = await db.execute(
        select(IncidentEvent)
        .where(IncidentEvent.incident_id == incident_id)
        .order_by(IncidentEvent.created_at)
    )
    return list(result.scalars().all())


async def add_comment(db: AsyncSession, incident_id: uuid.UUID, user_id: uuid.UUID, message: str) -> IncidentEvent:
    event = IncidentEvent(
        incident_id=incident_id, user_id=user_id, event_type=IncidentEventType.COMMENT, message=message
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)
    return event
