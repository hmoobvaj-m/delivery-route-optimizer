from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from delivery_route_api.models.optimization_job import OptimizationJob


class OptimizationJobRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
    
    async def create(
        self,
        *,
        route_id: UUID,
        algorithm: str = "ortools",
        parameters: dict[str, object] | None = None,
    ) -> OptimizationJob:
        job = OptimizationJob(
            route_id=route_id,
            status="pending",
            algorithm=algorithm,
            parameters=parameters or {},
        )
        
        self.session.add(job)
        await self.session.flush()
        await self.session.refresh(job)
        
        return job

    async def get(self, job_id: UUID) -> OptimizationJob | None:
        return await self.session.get(OptimizationJob, job_id)
    
    async def list_for_route(
        self,
        route_id: UUID,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[OptimizationJob]:
        statement = (
            select(OptimizationJob)
            .where(OptimizationJob.route_id == route_id)
            .order_by(OptimizationJob.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        
        res = await self.session.execute(statement)
        return list(res.scalars().all())