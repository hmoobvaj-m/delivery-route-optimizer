from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from delivery_route_api.models.optimization_job import OptimizationJob
from delivery_route_api.models.route import Route
from delivery_route_api.repositories.optimization_jobs import (
    OptimizationJobRepository,
)
from delivery_route_api.repositories.routes import RouteRepository
from delivery_route_api.services.routes import RouteNotFoundError

SUPPORTED_ALGORITHMS = frozenset({"ortools"})
MINIMUM_OPTIMIZATION_STOPS = 2


class InvalidOptimizationInputError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class StartOptimizationInput:
    route_id: UUID
    algorithm: str = "ortools"
    parameters: dict[str, object] = field(default_factory=dict)


class RouteRepositoryProtocol(Protocol):
    async def get(self, route_id: UUID) -> Route | None: ...


class OptimizationJobRepositoryProtocol(Protocol):
    async def create(
        self,
        *,
        route_id: UUID,
        algorithm: str = "ortools",
        parameters: dict[str, object] | None = None,
    ) -> OptimizationJob: ...

    async def get(self, job_id: UUID) -> OptimizationJob | None: ...

    async def list_for_route(
        self,
        route_id: UUID,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[OptimizationJob]: ...


class OptimizationService:
    def __init__(
        self,
        *,
        route_repository: RouteRepositoryProtocol,
        optimization_job_repository: OptimizationJobRepositoryProtocol,
    ) -> None:
        self.route_repository = route_repository
        self.optimization_job_repository = optimization_job_repository

    @classmethod
    def from_session(cls, session: AsyncSession) -> OptimizationService:
        return cls(
            route_repository=RouteRepository(session),
            optimization_job_repository=OptimizationJobRepository(session),
        )

    async def start_optimization(
        self,
        data: StartOptimizationInput,
    ) -> OptimizationJob:
        algorithm = data.algorithm.strip().lower()

        if algorithm not in SUPPORTED_ALGORITHMS:
            supported = ", ".join(sorted(SUPPORTED_ALGORITHMS))
            raise InvalidOptimizationInputError(
                f"Unsupported optimization algorithm. Supported algorithms: {supported}.",
            )

        route = await self.route_repository.get(data.route_id)

        if route is None:
            raise RouteNotFoundError(f"Route {data.route_id} was not found.")

        if route.original_stop_count < MINIMUM_OPTIMIZATION_STOPS:
            raise InvalidOptimizationInputError(
                "Route must contain at least 2 stops before optimization.",
            )

        return await self.optimization_job_repository.create(
            route_id=data.route_id,
            algorithm=algorithm,
            parameters=dict(data.parameters),
        )

    async def get_job(
        self,
        job_id: UUID,
    ) -> OptimizationJob | None:
        return await self.optimization_job_repository.get(job_id)

    async def list_jobs_for_route(
        self,
        route_id: UUID,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[OptimizationJob]:
        if limit < 1 or limit > 100:
            raise InvalidOptimizationInputError(
                "Limit must be between 1 and 100.",
            )

        if offset < 0:
            raise InvalidOptimizationInputError(
                "Offset cannot be negative.",
            )

        route = await self.route_repository.get(route_id)

        if route is None:
            raise RouteNotFoundError(f"Route {route_id} was not found.")

        return await self.optimization_job_repository.list_for_route(
            route_id,
            limit=limit,
            offset=offset,
        )