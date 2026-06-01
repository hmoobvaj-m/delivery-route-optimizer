# delivery-route-optimizer

A production-style delivery route optimization platform for experimenting with last-mile delivery routing, geospatial data, route comparison, and optimization workflows.

The project is being built as a monorepo with separate services for the API, optimization worker, frontend, infrastructure, and shared packages.

## Planned Stack

| Layer             | Technology           |
| ----------------- | -------------------- |
| Frontend          | Next.js + TypeScript |
| API               | FastAPI              |
| Optimization      | OR-Tools             |
| Routing Engine    | OSRM                 |
| Database          | PostgreSQL + PostGIS |
| Queue/Cache       | Redis                |
| Local Deployment  | Docker Compose       |
| Future Deployment | Kubernetes           |

## Repository Structure

```text
delivery-route-optimizer/
├── apps/
│   ├── api/                 # FastAPI backend service
│   ├── web/                 # Next.js frontend
│   └── worker/              # Optimization worker service
├── data/
│   └── osm/                 # Local OSM extracts and routing data
├── infrastructure/
│   ├── docker/              # Docker-related infrastructure files
│   └── kubernetes/          # Future Kubernetes manifests
├── packages/
│   └── shared/              # Shared schemas/types/utilities
├── docker-compose.yml
├── .env.example
└── README.md
```

## Local Development

### Prerequisites

* WSL Ubuntu 24.04
* Docker / Docker Compose
* Conda or Miniconda
* Python 3.12
* Git

### Python Environment

```bash
conda create -n delivery-ro python=3.12 -y
conda activate delivery-ro
python -m pip install -e "apps/api[dev]"
```

### Environment Variables

Copy the example environment file:

```bash
cp .env.example .env
```

Update `.env` with local-only credentials.

### Start Local Infrastructure

Start PostgreSQL/PostGIS and Redis:

```bash
docker compose up -d
docker compose ps
```

Verify PostGIS:

```bash
docker compose exec postgres sh -lc 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT PostGIS_Version();"'
```

Verify Redis:

```bash
docker compose exec redis redis-cli ping
```

Expected Redis response:

```text
PONG
```

### Run API Checks

```bash
ruff check apps/api
python -m pytest apps/api
```

### Run FastAPI Locally

```bash
uvicorn delivery_route_api.main:app --app-dir apps/api/src --reload --host 0.0.0.0 --port 8000
```

Verify the health endpoint:

```bash
curl -s http://localhost:8000/health && echo
```

Expected response:

```json
{"status":"ok","service":"api","env":"dev"}
```

### Optional JSON Formatting Tool

Install jq to pretty-print JSON responses from API endpoints:
```bash
sudo apt update
sudo apt install -y jq
```

Verify the health endpoint using jq:

```bash
curl -s http://localhost:8000/health | jq
```

Expected response:

```json
{
"status":"ok",
"service":"api",
"env":"dev"
}
```

## Current Development Workflow

This is currently a solo-development project. Direct pushes to `main` are allowed, but destructive operations such as force pushes and branch deletion should remain blocked.

Recommended workflow:

```bash
git switch main
git pull origin main

# make changes

ruff check apps/api
python -m pytest apps/api

git add .
git commit -m "type: concise description"
git push origin main
```

For larger or risky changes, create a feature branch first:

```bash
git switch -c feature/example-feature
```

## CI and Security

GitHub Actions currently runs:

* Repository structure checks
* Secret filename checks
* API linting with Ruff
* API tests with pytest
* CodeQL Python analysis

CodeQL is configured using advanced setup in:

```text
.github/workflows/security.yml
```

JavaScript/TypeScript CodeQL should be added later after the Next.js frontend exists under:

```text
apps/web/
```

## Current Implementation Status

Completed:

* Monorepo skeleton
* Docker Compose infrastructure for PostGIS and Redis
* FastAPI application skeleton
* `/health` endpoint
* API unit test
* Ruff linting
* GitHub Actions CI
* CodeQL Python security scan

Next major backend tasks:

1. Add structured logging.
2. Split `/health` and `/ready`.
3. Add SQLAlchemy async database connection.
4. Add Alembic migrations.
5. Define initial route, stop, job, sequence, and metrics models.
