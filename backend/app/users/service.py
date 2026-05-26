import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.users.models import User

logger = logging.getLogger(__name__)


async def get_or_create_user(
    db: AsyncSession,
    keycloak_id: uuid.UUID,
    email: str,
    username: str,
    role: str,
) -> User:
    result = await db.execute(select(User).where(User.id == keycloak_id))
    user = result.scalar_one_or_none()

    if user is None:
        user = User(id=keycloak_id, email=email, username=username, role=role)
        db.add(user)
        await db.commit()
        await db.refresh(user)
        logger.info("Provisioned user %s (%s)", email, role)
    elif user.role != role:
        user.role = role
        await db.commit()
        await db.refresh(user)

    return user


async def get_all_users(db: AsyncSession) -> list[User]:
    result = await db.execute(select(User).order_by(User.created_at))
    return list(result.scalars().all())


async def update_user_role(db: AsyncSession, user_id: uuid.UUID, role: str) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user:
        user.role = role
        await db.commit()
        await db.refresh(user)
    return user


async def delete_user(db: AsyncSession, user_id: uuid.UUID) -> bool:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user:
        await db.delete(user)
        await db.commit()
        return True
    return False
