from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from delivery_route_api.models.base import Base


class Route(Base):
    __tablename__ = "routes"

    __table_args__ = (
        CheckConstraint(
            "status IN ('draft', 'ready', 'optimizing', 'optimized', 'failed', 'archived')",
            name="route_status_valid",
        ),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft")
    source: Mapped[str] = mapped_column(String(64), nullable=False, default="manual")
    driver_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    original_stop_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    stops = relationship("Stop", back_populates="route", cascade="all, delete-orphan")
    optimization_jobs = relationship(
        "OptimizationJob",
        back_populates="route",
        cascade="all, delete-orphan",
    )
    sequences = relationship("RouteSequence", back_populates="route", cascade="all, delete-orphan")
    metrics = relationship("RouteMetric", back_populates="route", cascade="all, delete-orphan")
