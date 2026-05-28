import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.auth.rbac import Role, require_role
from app.core.database import get_db
from app.incidents import service as inc_service
from app.incidents.schemas import CommentCreate, IncidentEventRead, IncidentRead

router = APIRouter(prefix="/incidents", tags=["incidents"])


@router.get("", response_model=list[IncidentRead])
async def list_incidents(db: AsyncSession = Depends(get_db), _=Depends(get_current_user)):
    return await inc_service.get_all_incidents(db)


@router.get("/{incident_id}", response_model=IncidentRead)
async def get_incident(
    incident_id: uuid.UUID, db: AsyncSession = Depends(get_db), _=Depends(get_current_user)
):
    incident = await inc_service.get_incident(db, incident_id)
    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    return incident


@router.get("/{incident_id}/events", response_model=list[IncidentEventRead])
async def get_events(
    incident_id: uuid.UUID, db: AsyncSession = Depends(get_db), _=Depends(get_current_user)
):
    return await inc_service.get_incident_events(db, incident_id)


@router.post("/{incident_id}/acknowledge", response_model=IncidentRead)
async def acknowledge(
    incident_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_role(Role.ADMIN, Role.OPERATOR)),
):
    incident = await inc_service.acknowledge_incident(db, incident_id, user.id)
    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    return incident


@router.post("/{incident_id}/resolve", response_model=IncidentRead)
async def resolve(
    incident_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_role(Role.ADMIN, Role.OPERATOR)),
):
    incident = await inc_service.resolve_incident(db, incident_id, user.id)
    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    return incident


@router.post("/{incident_id}/comment", response_model=IncidentEventRead, status_code=status.HTTP_201_CREATED)
async def comment(
    incident_id: uuid.UUID,
    body: CommentCreate,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_role(Role.ADMIN, Role.OPERATOR)),
):
    return await inc_service.add_comment(db, incident_id, user.id, body.message)
