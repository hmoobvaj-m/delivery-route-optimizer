from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_serializer


class RouteCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    source: str = Field(default="manual", min_length=1, max_length=50)
    driver_id: str | None = Field(default=None, max_length=255)

class RouteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    source: str
    driver_id: str | None
    stop_count: int
    created_at: datetime
    updated_at: datetime

class StopCreateRequest(BaseModel):
    sequence_number: int = Field(ge=1)
    latitude: Decimal = Field(ge=Decimal("-90"), le=Decimal("90"))
    longitude: Decimal = Field(ge=Decimal("-180"), le=Decimal("180"))
    external_order_id: str | None = Field(default=None, max_length=255)
    address: str | None = Field(default=None, max_length=500)
    service_time_seconds: int = Field(default=120, ge=0)
    priority: int = Field(default=0, ge=0)
    time_window_start: datetime | None = None
    time_window_end: datetime | None = None
    notes: str | None = None

class StopResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    route_id: UUID
    sequence_number: int
    latitude: Decimal
    longitude: Decimal
    external_order_id: str | None
    address: str | None
    service_time_seconds: int
    priority: int
    time_window_start: datetime | None
    time_window_end: datetime | None
    notes: str | None
    created_at: datetime
    updated_at: datetime

    @field_serializer("latitude", "longitude")
    def serialize_decimal(self, value: Decimal) -> float:
        return float(value)
