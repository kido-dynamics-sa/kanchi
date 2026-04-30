"""Service utilities for Redis-backed company concurrency counters."""

from __future__ import annotations

import importlib
from dataclasses import dataclass
from typing import Any


@dataclass
class ConcurrencyEntry:
    """Single Redis counter entry."""

    key: str
    company_id: str
    value: int


class CompanyConcurrencyService:
    """Read company concurrency counters from Redis."""

    def __init__(self, redis_url: str | None, key_prefix: str = "company_concurrency:"):
        self.redis_url = redis_url
        self.key_prefix = key_prefix

    def list_entries(self, limit: int = 2000) -> list[ConcurrencyEntry]:
        """Return all counters matching the configured prefix."""
        if not self.redis_url:
            return []

        try:
            redis_module = importlib.import_module("redis")
            redis_exceptions = importlib.import_module("redis.exceptions")
        except ImportError:
            return []

        client = redis_module.Redis.from_url(self.redis_url, decode_responses=True)
        pattern = f"{self.key_prefix}*"

        try:
            keys = list(client.scan_iter(match=pattern, count=500))
        except redis_exceptions.RedisError:
            return []

        if limit > 0:
            keys = keys[:limit]

        if not keys:
            return []

        try:
            values = client.mget(keys)
        except redis_exceptions.RedisError:
            values = [None] * len(keys)

        entries: list[ConcurrencyEntry] = []
        for key, raw_value in zip(keys, values, strict=False):
            if not key:
                continue
            company_id = key[len(self.key_prefix) :] if key.startswith(self.key_prefix) else key
            entries.append(
                ConcurrencyEntry(
                    key=key,
                    company_id=company_id,
                    value=self._to_int(raw_value),
                )
            )

        return sorted(entries, key=lambda item: item.value, reverse=True)

    @staticmethod
    def _to_int(value: Any) -> int:
        if value is None:
            return 0
        try:
            return int(value)
        except (TypeError, ValueError):
            return 0
