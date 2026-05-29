import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, computed_field

from app.services.models import ServiceStatus

VALID_SEVERITIES = {"CRITICAL", "HIGH", "MEDIUM", "LOW"}


class ServiceCreate(BaseModel):
    name: str
    url: str
    description: str | None = None
    check_interval: int = 60
    timeout: int = 10
    failure_threshold: int = 2
    latency_threshold_ms: int = 2000
    incident_severity: str = "CRITICAL"


class ServiceUpdate(BaseModel):
    name: str | None = None
    url: str | None = None
    description: str | None = None
    check_interval: int | None = None
    timeout: int | None = None
    is_active: bool | None = None
    failure_threshold: int | None = None
    latency_threshold_ms: int | None = None
    incident_severity: str | None = None


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
    failure_threshold: int
    latency_threshold_ms: int
    incident_severity: str
    ssl_expires_at: datetime | None
    ssl_checked_at: datetime | None

    @computed_field
    @property
    def ssl_days_remaining(self) -> int | None:
        if self.ssl_expires_at is None:
            return None
        return (self.ssl_expires_at.replace(tzinfo=None) - datetime.utcnow()).days
