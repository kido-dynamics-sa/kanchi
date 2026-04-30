This file is a practical operating guide for coding agents working in this repository.

## Project Overview

Kanchi is a real-time Celery task monitoring system:

- Backend: FastAPI + SQLAlchemy + Alembic in `agent/`
- Frontend: Nuxt 4 (Vue 3 + TypeScript + Pinia) in `frontend/`
- Transport: REST API + WebSocket for live updates
- Data: SQLite by default, PostgreSQL/MySQL supported via `DATABASE_URL`

## First Steps For Agents

1. Read this file and `README.md`.
2. Prefer `make dev` from repo root for local development.
3. If changing backend API contracts, regenerate frontend API types.
4. Validate only what you changed (targeted checks first).

## Quick Commands

From repo root:

```bash
make dev         # backend + frontend in dev mode
make logs        # tail unified log file
make backend     # backend only
make frontend    # frontend only
```

From `agent/`:

```bash
poetry install
poetry run python app.py
poetry run python main.py --reload

poetry run black .
poetry run ruff check .
poetry run mypy .

poetry run alembic current
poetry run alembic upgrade head
poetry run alembic revision --autogenerate -m "message"

# backend tests
./run_tests.sh
```

From `frontend/`:

```bash
npm install
npm run dev
npm run build
npm run preview
npm run generate

# regenerate API types from backend OpenAPI
npm run generate:api:local
```

From `scripts/test-celery-app/`:

```bash
make start
make test-simple
make test-mixed
make test-stress
make test-failing
make status
make logs
```

## Architecture Map

Backend (`agent/`):

- `app.py`: FastAPI app creation, middleware, router wiring, lifecycle startup/shutdown.
- `main.py`: legacy entrypoint that runs `app:app` via uvicorn.
- `monitor.py`: Celery event ingestion.
- `event_handler.py`: maps incoming events to persistence + broadcast.
- `connection_manager.py`: WebSocket connections and broadcasting.
- `database.py`: DB engine/session/migration integration.
- `api/`: route modules (`task_routes.py`, `worker_routes.py`, `websocket_routes.py`, etc).
- `services/`: application/business logic.
- `security/`: auth manager, dependencies, token handling.
- `alembic/`: migrations.

Frontend (`frontend/`):

- `nuxt.config.ts`: runtime config (`apiUrl`, `wsUrl`, version).
- `app/stores/`: Pinia stores (`tasks`, `workers`, `websocket`, etc).
- `app/services/`: API and frontend services.
- `app/components/`: UI, layout, and domain components.
- `app/src/types/`: generated OpenAPI types.
- `generate-api-types.sh`: standard type generation script (axios template).

## Agent Rules

1. Keep changes scoped and minimal; avoid broad refactors unless asked.
2. Do not edit generated files directly:
	- `frontend/app/src/types/`
3. If backend route/request/response models change, regenerate frontend types.
4. Preserve real-time behavior:
	- event handler updates persistence
	- websocket broadcasts remain functional
	- frontend stores still handle both live and static data flows
5. Prefer extending existing service/store patterns over ad-hoc logic in routes/components.
6. Maintain Python line length 100 and existing lint/type standards.

## Environment Variables

Common backend env vars:

```bash
CELERY_BROKER_URL=amqp://guest:guest@localhost:5672//
DATABASE_URL=sqlite:///kanchi.db
WS_HOST=localhost
WS_PORT=8765
LOG_LEVEL=INFO
DEVELOPMENT_MODE=false

# security / auth
AUTH_ENABLED=false
AUTH_BASIC_ENABLED=false
AUTH_GOOGLE_ENABLED=false
AUTH_GITHUB_ENABLED=false
SESSION_SECRET_KEY=<set-in-production>
TOKEN_SECRET_KEY=<set-in-production>
```

Frontend runtime env vars:

```bash
NUXT_PUBLIC_API_URL=http://localhost:8765
NUXT_PUBLIC_WS_URL=ws://localhost:8765/ws
NUXT_PUBLIC_KANCHI_VERSION=dev
```

## Logging And Observability

- Unified backend/frontend file logging is enabled only when `DEVELOPMENT_MODE=true`.
- Log file defaults to `agent/kanchi.log`.
- `make logs` tails this file.
- Health endpoints:
  - `/api/health` (public)
  - `/api/health/details` (auth-protected when auth is enabled)

## Typical Change Workflows

### Add/Change Backend API

1. Update route/service/model in `agent/`.
2. Run focused backend checks.
3. Regenerate frontend API types:
	- `cd frontend && npm run generate:api:local`
4. Update frontend store/service consumers.
5. Smoke test critical UI flows and websockets.

### Add Database Fields

1. Update SQLAlchemy models.
2. Create Alembic migration.
3. Verify upgrade path with `alembic upgrade head`.
4. Update Pydantic schemas and API responses.

### Frontend Feature Work

1. Prefer store-driven state changes in `app/stores/`.
2. Keep API calls in service/store layer.
3. Reuse existing component patterns and utilities.

## Validation Checklist (Before Finishing)

Run only relevant checks for touched areas:

Backend-focused changes:

- `cd agent && poetry run ruff check .`
- `cd agent && poetry run mypy .`
- `cd agent && ./run_tests.sh` (or targeted tests)

Frontend-focused changes:

- `cd frontend && npm run build`

Integration-sensitive changes:

- Start app via `make dev`
- Confirm API reachable on `:8765`
- Confirm frontend reachable on `:3000` (dev) or served build as configured
- Confirm websocket-dependent UI updates still flow

## High-Impact Files

- `agent/app.py`
- `agent/config.py`
- `agent/event_handler.py`
- `agent/monitor.py`
- `agent/database.py`
- `agent/security/`
- `frontend/nuxt.config.ts`
- `frontend/app/stores/`
- `frontend/app/services/`

## Notes

- Root `docker-compose.yaml` builds and runs a full local containerized setup.
- `scripts/test-celery-app/` is useful for realistic broker/worker event generation.
- The frontend has its own deeper guide in `frontend/AGENTS.md`; use this root guide for repo-wide coordination and that file for frontend-specific conventions.
