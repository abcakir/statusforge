import uuid

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.monitoring.models import HealthCheck


async def get_health_history(db: AsyncSession, service_id: uuid.UUID, limit: int = 100) -> list[HealthCheck]:
    result = await db.execute(
        select(HealthCheck)
        .where(HealthCheck.service_id == service_id)
        .order_by(desc(HealthCheck.checked_at))
        .limit(limit)
    )
    return list(result.scalars().all())


async def create_health_check(db: AsyncSession, data: dict) -> HealthCheck:
    check = HealthCheck(**data)
    db.add(check)
    await db.commit()
    await db.refresh(check)
    return check
