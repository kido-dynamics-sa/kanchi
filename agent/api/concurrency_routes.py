"""API routes for company concurrency counters."""

from __future__ import annotations

from urllib.parse import urlparse, urlunparse

from fastapi import APIRouter, Depends, HTTPException, Query

from config import Config
from models import CompanyConcurrencyCounter
from security.dependencies import get_auth_dependency
from services.concurrency_service import CompanyConcurrencyService, ConcurrencyRedisError


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

        # An explicitly configured URL is trusted as-is (including whatever DB index
        # it already points at). The DB pin is only applied when we fall back to a
        # generic connection (REDIS_URL / the broker URL) that wasn't set up
        # specifically for this feature.
        if config.company_concurrency_redis_url:
            redis_url = config.company_concurrency_redis_url
        else:
            fallback_url = config.redis_url
            if not fallback_url and config.broker_url and config.broker_url.startswith("redis://"):
                fallback_url = config.broker_url
            redis_url = _redis_url_with_db(fallback_url, config.company_concurrency_redis_db)

        if not redis_url:
            raise HTTPException(
                status_code=503,
                detail=(
                    "Company concurrency Redis is not configured. Set "
                    "COMPANY_CONCURRENCY_REDIS_URL (or REDIS_URL) to the Redis instance "
                    "that stores company_concurrency:/company_outstanding_tasks: keys."
                ),
            )

        service = CompanyConcurrencyService(
            redis_url=redis_url,
            key_prefixes=[
                config.company_concurrency_prefix,
                config.company_outstanding_tasks_prefix,
            ],
        )
        try:
            entries = service.list_entries(limit=limit)
        except ConcurrencyRedisError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc

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
