import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.notifications.models import NotificationSeverity


class NotificationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    incident_id: uuid.UUID
    message: str
    severity: NotificationSeverity
    is_read: bool
    created_at: datetime
