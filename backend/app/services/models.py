import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import Boolean, Enum as SQLEnum, Integer, String, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ServiceStatus(str, Enum):
    UNKNOWN = "UNKNOWN"
    UP = "UP"
    DOWN = "DOWN"
    DEGRADED = "DEGRADED"


class MonitoredService(Base):
    __tablename__ = "monitored_services"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    description: Mapped[str | None] = mapped_column(String(1024))
    check_interval: Mapped[int] = mapped_column(Integer, default=60)
    timeout: Mapped[int] = mapped_column(Integer, default=10)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    status: Mapped[ServiceStatus] = mapped_column(
        SQLEnum(ServiceStatus, name="servicestatus"), default=ServiceStatus.UNKNOWN
    )
    consecutive_failures: Mapped[int] = mapped_column(Integer, default=0)
    last_checked_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Alert rule thresholds
    failure_threshold: Mapped[int] = mapped_column(Integer, default=2)
    latency_threshold_ms: Mapped[int] = mapped_column(Integer, default=2000)
    incident_severity: Mapped[str] = mapped_column(String(20), default="CRITICAL")

    # SSL certificate info
    ssl_expires_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))
    ssl_checked_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))
