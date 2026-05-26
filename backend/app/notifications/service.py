import uuid

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.notifications.models import Notification, NotificationSeverity
from app.users.models import User


async def create_notifications_for_incident(
    db: AsyncSession,
    incident_id: uuid.UUID,
    message: str,
    severity: NotificationSeverity,
) -> None:
    result = await db.execute(
        select(User).where(User.role.in_(["ADMIN", "OPERATOR"]), User.is_active == True)
    )
    for user in result.scalars().all():
        db.add(Notification(user_id=user.id, incident_id=incident_id, message=message, severity=severity))
    await db.commit()


async def get_user_notifications(db: AsyncSession, user_id: uuid.UUID) -> list[Notification]:
    result = await db.execute(
        select(Notification)
        .where(Notification.user_id == user_id)
        .order_by(desc(Notification.created_at))
        .limit(50)
    )
    return list(result.scalars().all())


async def mark_read(db: AsyncSession, notification_id: uuid.UUID, user_id: uuid.UUID) -> Notification | None:
    result = await db.execute(
        select(Notification).where(Notification.id == notification_id, Notification.user_id == user_id)
    )
    n = result.scalar_one_or_none()
    if n:
        n.is_read = True
        await db.commit()
        await db.refresh(n)
    return n


async def mark_all_read(db: AsyncSession, user_id: uuid.UUID) -> None:
    result = await db.execute(
        select(Notification).where(Notification.user_id == user_id, Notification.is_read == False)
    )
    for n in result.scalars().all():
        n.is_read = True
    await db.commit()
