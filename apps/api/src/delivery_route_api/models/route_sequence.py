from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from delivery_route_api.models.base import Base


class RouteSequence(Base):
    __tablename__ = "route_sequences"

    __table_args__ = (
        CheckConstraint(
            "sequence_type IN ('original', 'optimized', 'driver_adjusted')",
            name="route_sequence_type_valid",
        ),
        Index(
            "ix_route_sequences_route_type_position",
            "route_id",
            "sequence_type",
            "position",
            unique=True,
        ),
        Index(
            "ix_route_sequences_route_type_stop",
            "route_id",
            "sequence_type",
            "stop_id",
            unique=True,
        ),
    )

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    route_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("routes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    stop_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("stops.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    optimization_job_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("optimization_jobs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    sequence_type: Mapped[str] = mapped_column(String(32), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    route = relationship("Route", back_populates="sequences")
    stop = relationship("Stop", back_populates="sequences")
    optimization_job = relationship("OptimizationJob", back_populates="sequences")
