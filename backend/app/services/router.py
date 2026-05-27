import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.auth.rbac import Role, require_role
from app.core.database import get_db
from app.monitoring import service as mon_service
from app.monitoring.schemas import HealthCheckRead
from app.services import service as svc_service
from app.services.schemas import ServiceCreate, ServiceRead, ServiceUpdate

router = APIRouter(prefix="/services", tags=["services"])


@router.get("", response_model=list[ServiceRead])
async def list_services(db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    return await svc_service.get_all_services(db)


@router.post("", response_model=ServiceRead, status_code=status.HTTP_201_CREATED)
async def create_service(
    data: ServiceCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_role(Role.ADMIN, Role.OPERATOR)),
):
    return await svc_service.create_service(db, data.model_dump())


@router.get("/{service_id}", response_model=ServiceRead)
async def get_service(
    service_id: uuid.UUID, db: AsyncSession = Depends(get_db), _=Depends(get_current_user)
):
    svc = await svc_service.get_service(db, service_id)
    if not svc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")
    return svc


@router.patch("/{service_id}", response_model=ServiceRead)
async def update_service(
    service_id: uuid.UUID,
    data: ServiceUpdate,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_role(Role.ADMIN, Role.OPERATOR)),
):
    svc = await svc_service.update_service(db, service_id, data.model_dump(exclude_none=True))
    if not svc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")
    return svc


@router.delete("/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_service(
    service_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_role(Role.ADMIN)),
):
    if not await svc_service.delete_service(db, service_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")


@router.get("/{service_id}/health-history", response_model=list[HealthCheckRead])
async def health_history(
    service_id: uuid.UUID,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    _=Depends(get_current_user),
):
    return await mon_service.get_health_history(db, service_id, limit)


@router.post("/{service_id}/check-now", status_code=status.HTTP_202_ACCEPTED)
async def check_now(
    service_id: uuid.UUID,
    _=Depends(require_role(Role.ADMIN, Role.OPERATOR)),
):
    from app.tasks.health_check import check_service
    check_service.delay(str(service_id), force=True)
    return {"message": "Check triggered"}
