from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from delivery_route_api.database import get_database_session
from delivery_route_api.schemas.routes import (
    RouteCreateRequest,
    RouteResponse,
    StopCreateRequest,
    StopResponse,
)
from delivery_route_api.services.routes import (
    CreateRouteInput,
    CreateStopInput,
    InvalidRouteInputError,
    RouteNotFoundError,
    RouteService,
)

router = APIRouter(prefix="/routes", tags=["routes"])


DatabaseSessionDependency = Annotated[
    AsyncSession,
    Depends(get_database_session),
]


def get_route_service(session: DatabaseSessionDependency) -> RouteService:
    return RouteService.from_session(session)


RouteServiceDependency = Annotated[
    RouteService,
    Depends(get_route_service),
]


@router.post(
    "",
    response_model=RouteResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_route(
    payload: RouteCreateRequest,
    service: RouteServiceDependency,
) -> RouteResponse:
    try:
        route = await service.create_route(
            CreateRouteInput(
                name=payload.name,
                source=payload.source,
                driver_id=payload.driver_id,
            ),
        )
    except InvalidRouteInputError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return route


@router.get(
    "/{route_id}",
    response_model=RouteResponse,
)
async def get_route(
    route_id: UUID,
    service: RouteServiceDependency,
) -> RouteResponse:
    route = await service.get_route(route_id)

    if route is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Route not found.",
        )

    return route


@router.post(
    "/{route_id}/stops",
    response_model=StopResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_stop(
    route_id: UUID,
    payload: StopCreateRequest,
    service: RouteServiceDependency,
) -> StopResponse:
    try:
        stop = await service.add_stop(
            CreateStopInput(
                route_id=route_id,
                sequence_number=payload.sequence_number,
                latitude=payload.latitude,
                longitude=payload.longitude,
                external_order_id=payload.external_order_id,
                address=payload.address,
                service_time_seconds=payload.service_time_seconds,
                priority=payload.priority,
                time_window_start=payload.time_window_start,
                time_window_end=payload.time_window_end,
                notes=payload.notes,
            ),
        )
    except RouteNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Route not found.",
        ) from exc
    except InvalidRouteInputError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return stop


@router.get(
    "/{route_id}/stops",
    response_model=list[StopResponse],
)
async def list_stops(
    route_id: UUID,
    service: RouteServiceDependency,
) -> list[StopResponse]:
    try:
        return await service.list_stops(route_id)
    except RouteNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Route not found.",
        ) from exc
