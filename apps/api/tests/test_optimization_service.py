from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID, uuid4

import pytest

from delivery_route_api.services.optimization import (
    InvalidOptimizationInputError,
    OptimizationService,
    StartOptimizationInput,
)
from delivery_route_api.services.routes import RouteNotFoundError


@dataclass(slots=True)
class FakeRoute:
    id: UUID
    original_stop_count: int


@dataclass(slots=True)
class FakeOptimizationJob:
    id: UUID
    route_id: UUID
    status: str
    algorithm: str
    parameters: dict[str, object]


class FakeRouteRepository:
    def __init__(self, route: FakeRoute | None = None) -> None:
        self.route = route
        self.requested_route_ids: list[UUID] = []

    async def get(self, route_id: UUID) -> FakeRoute | None:
        self.requested_route_ids.append(route_id)

        if self.route is None or self.route.id != route_id:
            return None

        return self.route


class FakeOptimizationJobRepository:
    def __init__(self) -> None:
        self.jobs: dict[UUID, FakeOptimizationJob] = {}
        self.created_jobs: list[FakeOptimizationJob] = []
        self.list_calls: list[tuple[UUID, int, int]] = []

    async def create(
        self,
        *,
        route_id: UUID,
        algorithm: str = "ortools",
        parameters: dict[str, object] | None = None,
    ) -> FakeOptimizationJob:
        job = FakeOptimizationJob(
            id=uuid4(),
            route_id=route_id,
            status="pending",
            algorithm=algorithm,
            parameters=parameters or {},
        )

        self.jobs[job.id] = job
        self.created_jobs.append(job)
        return job

    async def get(self, job_id: UUID) -> FakeOptimizationJob | None:
        return self.jobs.get(job_id)

    async def list_for_route(
        self,
        route_id: UUID,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[FakeOptimizationJob]:
        self.list_calls.append((route_id, limit, offset))

        matching_jobs = [
            job
            for job in self.jobs.values()
            if job.route_id == route_id
        ]

        return matching_jobs[offset : offset + limit]


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


def build_service(
    *,
    route: FakeRoute | None,
) -> tuple[
    OptimizationService,
    FakeRouteRepository,
    FakeOptimizationJobRepository,
]:
    route_repository = FakeRouteRepository(route)
    job_repository = FakeOptimizationJobRepository()

    service = OptimizationService(
        route_repository=route_repository,
        optimization_job_repository=job_repository,
    )

    return service, route_repository, job_repository


@pytest.mark.anyio
async def test_start_optimization_creates_pending_job() -> None:
    route_id = uuid4()
    route = FakeRoute(
        id=route_id,
        original_stop_count=3,
    )
    service, _, job_repository = build_service(route=route)

    parameters = {
        "vehicle_count": 1,
        "return_to_depot": True,
    }

    job = await service.start_optimization(
        StartOptimizationInput(
            route_id=route_id,
            algorithm=" ORTOOLS ",
            parameters=parameters,
        ),
    )

    assert job.route_id == route_id
    assert job.status == "pending"
    assert job.algorithm == "ortools"
    assert job.parameters == parameters
    assert job is job_repository.created_jobs[0]


@pytest.mark.anyio
async def test_start_optimization_copies_parameters() -> None:
    route_id = uuid4()
    route = FakeRoute(
        id=route_id,
        original_stop_count=2,
    )
    service, _, _ = build_service(route=route)

    parameters: dict[str, object] = {"vehicle_count": 1}

    job = await service.start_optimization(
        StartOptimizationInput(
            route_id=route_id,
            parameters=parameters,
        ),
    )

    parameters["vehicle_count"] = 99

    assert job.parameters == {"vehicle_count": 1}


@pytest.mark.anyio
async def test_start_optimization_rejects_missing_route() -> None:
    route_id = uuid4()
    service, _, job_repository = build_service(route=None)

    with pytest.raises(RouteNotFoundError, match="was not found"):
        await service.start_optimization(
            StartOptimizationInput(route_id=route_id),
        )

    assert job_repository.created_jobs == []


@pytest.mark.anyio
async def test_start_optimization_requires_two_stops() -> None:
    route_id = uuid4()
    route = FakeRoute(
        id=route_id,
        original_stop_count=1,
    )
    service, _, job_repository = build_service(route=route)

    with pytest.raises(
        InvalidOptimizationInputError,
        match="at least 2 stops",
    ):
        await service.start_optimization(
            StartOptimizationInput(route_id=route_id),
        )

    assert job_repository.created_jobs == []


@pytest.mark.anyio
async def test_start_optimization_rejects_unsupported_algorithm() -> None:
    route_id = uuid4()
    route = FakeRoute(
        id=route_id,
        original_stop_count=3,
    )
    service, route_repository, job_repository = build_service(route=route)

    with pytest.raises(
        InvalidOptimizationInputError,
        match="Unsupported optimization algorithm",
    ):
        await service.start_optimization(
            StartOptimizationInput(
                route_id=route_id,
                algorithm="unknown",
            ),
        )

    assert route_repository.requested_route_ids == []
    assert job_repository.created_jobs == []


@pytest.mark.anyio
async def test_get_job_returns_repository_result() -> None:
    route_id = uuid4()
    route = FakeRoute(
        id=route_id,
        original_stop_count=2,
    )
    service, _, job_repository = build_service(route=route)

    created_job = await job_repository.create(
        route_id=route_id,
        algorithm="ortools",
        parameters={},
    )

    result = await service.get_job(created_job.id)

    assert result is created_job


@pytest.mark.anyio
async def test_list_jobs_for_route_uses_pagination() -> None:
    route_id = uuid4()
    route = FakeRoute(
        id=route_id,
        original_stop_count=3,
    )
    service, route_repository, job_repository = build_service(route=route)

    expected_job = await job_repository.create(
        route_id=route_id,
        algorithm="ortools",
        parameters={},
    )

    result = await service.list_jobs_for_route(
        route_id,
        limit=25,
        offset=0,
    )

    assert result == [expected_job]
    assert route_repository.requested_route_ids == [route_id]
    assert job_repository.list_calls == [(route_id, 25, 0)]


@pytest.mark.anyio
async def test_list_jobs_for_missing_route_raises_error() -> None:
    route_id = uuid4()
    service, _, job_repository = build_service(route=None)

    with pytest.raises(RouteNotFoundError, match="was not found"):
        await service.list_jobs_for_route(route_id)

    assert job_repository.list_calls == []


@pytest.mark.anyio
@pytest.mark.parametrize("limit", [0, 101])
async def test_list_jobs_rejects_invalid_limit(limit: int) -> None:
    route_id = uuid4()
    route = FakeRoute(
        id=route_id,
        original_stop_count=2,
    )
    service, route_repository, job_repository = build_service(route=route)

    with pytest.raises(
        InvalidOptimizationInputError,
        match="Limit must be between 1 and 100",
    ):
        await service.list_jobs_for_route(
            route_id,
            limit=limit,
        )

    assert route_repository.requested_route_ids == []
    assert job_repository.list_calls == []


@pytest.mark.anyio
async def test_list_jobs_rejects_negative_offset() -> None:
    route_id = uuid4()
    route = FakeRoute(
        id=route_id,
        original_stop_count=2,
    )
    service, route_repository, job_repository = build_service(route=route)

    with pytest.raises(
        InvalidOptimizationInputError,
        match="Offset cannot be negative",
    ):
        await service.list_jobs_for_route(
            route_id,
            offset=-1,
        )

    assert route_repository.requested_route_ids == []
    assert job_repository.list_calls == []