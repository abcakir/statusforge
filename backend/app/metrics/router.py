import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.core.database import get_db
from app.metrics import service as metrics_service

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("/overview")
async def overview(db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    return await metrics_service.get_overview(db)


@router.get("/services/{service_id}/latency")
async def latency_series(
    service_id: uuid.UUID, hours: int = 24, db: AsyncSession = Depends(get_db), _=Depends(get_current_user)
):
    return await metrics_service.get_latency_series(db, service_id, hours)


@router.get("/services/{service_id}/uptime")
async def uptime(
    service_id: uuid.UUID, days: int = 30, db: AsyncSession = Depends(get_db), _=Depends(get_current_user)
):
    return await metrics_service.get_uptime(db, service_id, days)
