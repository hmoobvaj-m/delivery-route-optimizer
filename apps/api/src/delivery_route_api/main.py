from fastapi import FastAPI
from delivery_route_api.config import get_settings

settings = get_settings()

app = FastAPI(
    title="Delivery Route Optimizer API",
    version="0.1.0",
    description="Backend API for route optimnization, routing jobs, and delivery route data"
)

@app.get("/health", tags=["system"])
def health_check() ->  dict[str, str]:
    return {
        "status": "ok",
        "service": "api",
        "env": settings.app_env,
    }