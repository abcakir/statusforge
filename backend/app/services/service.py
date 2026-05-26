import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.models import MonitoredService


async def get_all_services(db: AsyncSession) -> list[MonitoredService]:
    result = await db.execute(select(MonitoredService).order_by(MonitoredService.created_at))
    return list(result.scalars().all())


async def get_service(db: AsyncSession, service_id: uuid.UUID) -> MonitoredService | None:
    result = await db.execute(select(MonitoredService).where(MonitoredService.id == service_id))
    return result.scalar_one_or_none()


async def create_service(db: AsyncSession, data: dict) -> MonitoredService:
    svc = MonitoredService(**data)
    db.add(svc)
    await db.commit()
    await db.refresh(svc)
    return svc


async def update_service(db: AsyncSession, service_id: uuid.UUID, data: dict) -> MonitoredService | None:
    svc = await get_service(db, service_id)
    if not svc:
        return None
    for k, v in data.items():
        setattr(svc, k, v)
    await db.commit()
    await db.refresh(svc)
    return svc


async def delete_service(db: AsyncSession, service_id: uuid.UUID) -> bool:
    svc = await get_service(db, service_id)
    if not svc:
        return False
    await db.delete(svc)
    await db.commit()
    return True
