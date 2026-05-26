import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.incidents.models import IncidentEventType, IncidentSeverity, IncidentStatus


class IncidentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    service_id: uuid.UUID
    title: str
    status: IncidentStatus
    severity: IncidentSeverity
    started_at: datetime
    resolved_at: datetime | None
    created_at: datetime


class IncidentEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    incident_id: uuid.UUID
    user_id: uuid.UUID | None
    event_type: IncidentEventType
    message: str | None
    created_at: datetime


class CommentCreate(BaseModel):
    message: str
