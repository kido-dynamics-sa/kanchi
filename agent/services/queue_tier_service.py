"""Utilities for classifying Celery queues into priority tiers.

Queue naming convention observed in kidoapp's queue routing
(company_bucket_<NN>_<tier>, tier one of fast/medium/slow). Queues that
don't match this pattern (e.g. "default") are left unclassified.
"""

from __future__ import annotations

import re

QUEUE_TIERS = ["fast", "medium", "slow"]

_QUEUE_TIER_PATTERN = re.compile(r"^company_bucket_\d+_(fast|medium|slow)$")


def parse_queue_tier(queue_name: str) -> str | None:
    """Return the priority tier encoded in a queue name, or None if unrecognized."""
    match = _QUEUE_TIER_PATTERN.match(queue_name)
    return match.group(1) if match else None
