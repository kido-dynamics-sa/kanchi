"""API routes for company concurrency counters."""

from __future__ import annotations

from urllib.parse import urlparse, urlunparse

from fastapi import APIRouter, Depends, Query

from config import Config
from models import CompanyConcurrencyCounter
from security.dependencies import get_auth_dependency
from services.concurrency_service import CompanyConcurrencyService


def _redis_url_with_db(redis_url: str | None, db_index: int) -> str | None:
    """Return a Redis URL pinned to the provided DB index."""
    if not redis_url:
        return None

    parsed = urlparse(redis_url)
    if parsed.scheme not in {"redis", "rediss"}:
        return redis_url

    return urlunparse(parsed._replace(path=f"/{db_index}"))


def create_router(app_state) -> APIRouter:
    """Create company concurrency API routes."""
    router = APIRouter()

    require_user_dep = get_auth_dependency(app_state, require=True)

    @router.get(
        "/api/concurrency/company",
        response_model=list[CompanyConcurrencyCounter],
    )
    async def list_company_concurrency(
        limit: int = Query(default=2000, ge=1, le=10000),
        _current_user=Depends(require_user_dep),
    ):
        """List all Redis counters for company concurrency and outstanding tasks."""
        config = app_state.config or Config.from_env()

        redis_url = config.company_concurrency_redis_url or config.redis_url
        if not redis_url and config.broker_url and config.broker_url.startswith("redis://"):
            redis_url = config.broker_url

        redis_url = _redis_url_with_db(redis_url, config.company_concurrency_redis_db)

        service = CompanyConcurrencyService(
            redis_url=redis_url,
            key_prefixes=[
                config.company_concurrency_prefix,
                config.company_outstanding_tasks_prefix,
            ],
        )
        entries = service.list_entries(limit=limit)

        return [
            {
                "key": item.key,
                "company_id": item.company_id,
                "counter_type": item.counter_type,
                "value": item.value,
            }
            for item in entries
        ]

    return router
