import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.services.models import ServiceStatus


class ServiceCreate(BaseModel):
    name: str
    url: str
    description: str | None = None
    check_interval: int = 60
    timeout: int = 10


class ServiceUpdate(BaseModel):
    name: str | None = None
    url: str | None = None
    description: str | None = None
    check_interval: int | None = None
    timeout: int | None = None
    is_active: bool | None = None


class ServiceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    url: str
    description: str | None
    check_interval: int
    timeout: int
    is_active: bool
    status: ServiceStatus
    consecutive_failures: int
    last_checked_at: datetime | None
    created_at: datetime
