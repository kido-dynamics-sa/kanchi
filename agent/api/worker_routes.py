"""API routes for worker-related endpoints."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from config import Config
from models import WorkerInfo
from security.dependencies import get_auth_dependency
from services import WorkerService


def _get_worker_queue_subscriptions(app_state) -> dict[str, list[str]]:
    """Return worker -> subscribed queue names from Celery inspect API."""
    if not app_state.monitor_instance:
        return {}

    try:
        inspect_result = app_state.monitor_instance.app.control.inspect(timeout=1.0).active_queues()
    except Exception:  # pylint: disable=broad-except
        return {}

    if not inspect_result:
        return {}

    subscriptions: dict[str, list[str]] = {}
    for hostname, queues in inspect_result.items():
        queue_names = sorted({q.get("name") for q in queues or [] if q.get("name")})
        subscriptions[hostname] = queue_names

    return subscriptions


def create_router(app_state) -> APIRouter:
    """Create worker router with dependency injection."""
    router = APIRouter(prefix="/api", tags=["workers"])

    config = app_state.config or Config.from_env()
    require_user_dep = get_auth_dependency(app_state, require=True)

    if config.auth_enabled:
        router.dependencies.append(Depends(require_user_dep))

    def get_db() -> Session:
        """FastAPI dependency for database sessions."""
        if not app_state.db_manager:
            raise HTTPException(status_code=500, detail="Database not initialized")
        with app_state.db_manager.get_session() as session:
            yield session

    @router.get("/workers", response_model=list[WorkerInfo])
    async def get_workers(session: Session = Depends(get_db)):
        """Get information about all workers."""
        monitor_workers_data = (
            app_state.monitor_instance.get_workers_info() if app_state.monitor_instance else {}
        )
        queue_subscriptions = _get_worker_queue_subscriptions(app_state)

        worker_service = WorkerService(session)
        persisted_workers_data = worker_service.get_latest_workers_snapshot()

        all_hostnames = sorted(
            set(monitor_workers_data.keys())
            | set(persisted_workers_data.keys())
            | set(queue_subscriptions.keys())
        )
        worker_list = []

        for hostname in all_hostnames:
            monitor_data = monitor_workers_data.get(hostname, {})
            persisted_data = persisted_workers_data.get(hostname, {})

            data = {**persisted_data, **monitor_data}

            worker_info = WorkerInfo(
                hostname=hostname,
                status=data.get("status", "unknown"),
                timestamp=data.get("timestamp", datetime.now(timezone.utc)),
                active_tasks=data.get("active", 0),
                processed_tasks=data.get("processed", 0),
                sw_ident=data.get("sw_ident"),
                sw_ver=data.get("sw_ver"),
                sw_sys=data.get("sw_sys"),
                loadavg=data.get("loadavg"),
                freq=data.get("freq"),
                queues_subscribed=queue_subscriptions.get(hostname, []),
            )
            worker_list.append(worker_info)

        return worker_list

    @router.get("/workers/{hostname}", response_model=WorkerInfo)
    async def get_worker(hostname: str, session: Session = Depends(get_db)):
        """Get information about a specific worker."""
        monitor_workers_data = (
            app_state.monitor_instance.get_workers_info() if app_state.monitor_instance else {}
        )
        queue_subscriptions = _get_worker_queue_subscriptions(app_state)
        persisted_workers_data = WorkerService(session).get_latest_workers_snapshot()

        monitor_data = monitor_workers_data.get(hostname)
        persisted_data = persisted_workers_data.get(hostname)
        queue_data = queue_subscriptions.get(hostname)

        if not monitor_data and not persisted_data and queue_data is None:
            raise HTTPException(status_code=404, detail="Worker not found")

        data = {**(persisted_data or {}), **(monitor_data or {})}

        return WorkerInfo(
            hostname=hostname,
            status=data.get("status", "unknown"),
            timestamp=data.get("timestamp", datetime.now(timezone.utc)),
            active_tasks=data.get("active", 0),
            processed_tasks=data.get("processed", 0),
            sw_ident=data.get("sw_ident"),
            sw_ver=data.get("sw_ver"),
            sw_sys=data.get("sw_sys"),
            loadavg=data.get("loadavg"),
            freq=data.get("freq"),
            queues_subscribed=queue_data or [],
        )

    @router.get("/workers/events/recent")
    async def get_recent_worker_events(limit: int = 50, session: Session = Depends(get_db)):
        """Get recent worker events."""
        worker_service = WorkerService(session)
        return worker_service.get_recent_worker_events(limit)

    return router
