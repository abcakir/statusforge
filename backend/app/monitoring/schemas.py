import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.monitoring.models import CheckStatus


class HealthCheckRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    service_id: uuid.UUID
    status: CheckStatus
    latency_ms: float | None
    status_code: int | None
    error: str | None
    checked_at: datetime
