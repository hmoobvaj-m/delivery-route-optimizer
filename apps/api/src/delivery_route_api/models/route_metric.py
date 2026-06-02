from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from delivery_route_api.models.base import Base


class RouteMetric(Base):
    __tablename__ = "route_metrics"

    __table_args__ = (
        CheckConstraint(
            "metric_type IN ('original', 'optimized', 'comparison')",
            name="route_metric_type_valid",
        ),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    route_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("routes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    optimization_job_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("optimization_jobs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    metric_type: Mapped[str] = mapped_column(String(32), nullable=False)

    total_distance_meters: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_duration_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    drive_duration_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    service_duration_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    backtrack_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    estimated_savings_distance_meters: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    estimated_savings_duration_seconds: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    route = relationship("Route", back_populates="metrics")
    optimization_job = relationship("OptimizationJob", back_populates="metrics")
