"""Service utilities for Redis-backed company concurrency counters."""

from __future__ import annotations

import importlib
from dataclasses import dataclass
from typing import Any


class ConcurrencyRedisError(RuntimeError):
    """Raised when the Redis backend for concurrency counters is unreachable/unusable."""


@dataclass
class ConcurrencyEntry:
    """Single Redis counter entry."""

    key: str
    company_id: str
    counter_type: str
    value: int


class CompanyConcurrencyService:
    """Read company concurrency counters from Redis."""

    def __init__(
        self,
        redis_url: str | None,
        key_prefixes: list[str] | tuple[str, ...] | None = None,
    ):
        self.redis_url = redis_url
        if key_prefixes:
            self.key_prefixes = [prefix for prefix in key_prefixes if prefix]
        else:
            self.key_prefixes = ["company_concurrency:", "company_outstanding_tasks:"]

    def list_entries(self, limit: int = 2000) -> list[ConcurrencyEntry]:
        """Return all counters matching the configured prefixes."""
        if not self.redis_url or not self.key_prefixes:
            return []

        try:
            redis_module = importlib.import_module("redis")
            redis_exceptions = importlib.import_module("redis.exceptions")
        except ImportError as exc:
            raise ConcurrencyRedisError(
                "The 'redis' package is not installed on the server."
            ) from exc

        client = redis_module.Redis.from_url(
            self.redis_url, decode_responses=True, socket_connect_timeout=3
        )

        try:
            client.ping()
        except redis_exceptions.RedisError as exc:
            raise ConcurrencyRedisError(f"Could not connect to Redis: {exc}") from exc

        keys: list[str] = []
        key_prefix_by_key: dict[str, str] = {}
        for prefix in self.key_prefixes:
            pattern = f"{prefix}*"
            try:
                for key in client.scan_iter(match=pattern, count=500):
                    if key not in key_prefix_by_key:
                        key_prefix_by_key[key] = prefix
                        keys.append(key)
            except redis_exceptions.RedisError:
                continue

        if limit > 0 and len(keys) > limit:
            keys = keys[:limit]

        if not keys:
            return []

        values = self._read_counter_values(client, keys, redis_exceptions)

        entries: list[ConcurrencyEntry] = []
        for key, raw_value in zip(keys, values, strict=False):
            if not key:
                continue
            prefix = key_prefix_by_key.get(key, "")
            company_id = key[len(prefix) :] if prefix and key.startswith(prefix) else key
            counter_type = prefix.removesuffix(":") if prefix else "unknown"
            entries.append(
                ConcurrencyEntry(
                    key=key,
                    company_id=company_id,
                    counter_type=counter_type,
                    value=self._to_int(raw_value),
                )
            )

        return sorted(entries, key=lambda item: item.value, reverse=True)

    @staticmethod
    def _read_counter_values(
        client: Any, keys: list[str], redis_exceptions: Any
    ) -> list[int | None]:
        """Read values using type-appropriate Redis commands.

        Outstanding task counters are often stored as Redis sorted sets, which require
        ZCARD instead of GET/MGET.
        """
        if not keys:
            return []

        values: list[int | None] = []
        for key in keys:
            try:
                key_type = client.type(key)
            except redis_exceptions.RedisError:
                values.append(None)
                continue

            try:
                if key_type == "zset":
                    values.append(int(client.zcard(key)))
                elif key_type == "set":
                    values.append(int(client.scard(key)))
                elif key_type == "string":
                    values.append(client.get(key))
                elif key_type == "hash":
                    values.append(int(client.hlen(key)))
                elif key_type == "list":
                    values.append(int(client.llen(key)))
                else:
                    values.append(client.get(key))
            except redis_exceptions.RedisError:
                values.append(None)

        return values

    @staticmethod
    def _to_int(value: Any) -> int:
        if value is None:
            return 0
        try:
            return int(value)
        except (TypeError, ValueError):
            return 0
