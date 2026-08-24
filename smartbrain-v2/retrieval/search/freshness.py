"""Freshness tracking utilities for the Engineering Memory Graph.

Provides staleness detection for individual entities and aggregate freshness
summaries across the entire graph.

Requirements: 4.1, 4.2, 4.3, 4.4
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from config.settings import get_settings


def check_staleness(
    updated_at: str | datetime | None,
    threshold_hours: int | None = None,
) -> str | None:
    """Determine if an entity is stale based on its updated_at timestamp.

    Args:
        updated_at: The entity's updated_at value (ISO string, datetime, or None).
        threshold_hours: Hours after which an entity is considered stale.
            Defaults to the configured ``staleness_threshold_hours`` setting.

    Returns:
        ``"stale"`` if the entity exceeds the staleness threshold, ``None`` otherwise.
    """
    if threshold_hours is None:
        settings = get_settings()
        threshold_hours = settings.staleness_threshold_hours

    if updated_at is None:
        return "stale"

    if isinstance(updated_at, str):
        try:
            dt = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return "stale"
    elif isinstance(updated_at, datetime):
        dt = updated_at
    else:
        return "stale"

    # Ensure timezone-aware comparison
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)

    now = datetime.now(UTC)
    age_hours = (now - dt).total_seconds() / 3600

    if age_hours > threshold_hours:
        return "stale"
    return None


async def get_freshness_summary(driver: Any) -> dict[str, Any]:
    """Query Neo4j for aggregate freshness statistics.

    Counts entities by their ``updated_at`` timestamp relative to now:
    - Percentage updated within the last hour
    - Percentage updated within the last 24 hours
    - Percentage older than 24 hours
    - Total entity count

    Args:
        driver: An async Neo4j driver instance.

    Returns:
        A dict with keys ``updated_within_1h``, ``updated_within_24h``,
        ``older_than_24h``, and ``total_entities``.
    """
    query = """
    MATCH (n)
    WHERE n.source_id IS NOT NULL AND n.deleted_at IS NULL
    WITH n,
         CASE
           WHEN n.updated_at IS NULL THEN 'old'
           WHEN datetime(n.updated_at) > datetime() - duration({hours: 1}) THEN 'within_1h'
           WHEN datetime(n.updated_at) > datetime() - duration({hours: 24}) THEN 'within_24h'
           ELSE 'old'
         END AS bucket
    RETURN bucket, count(n) AS cnt
    """

    total = 0
    within_1h = 0
    within_24h = 0
    older = 0

    async with driver.session() as session:
        result = await session.run(query)
        records = await result.data()

    for record in records:
        bucket = record["bucket"]
        cnt = record["cnt"]
        total += cnt
        if bucket == "within_1h":
            within_1h = cnt
        elif bucket == "within_24h":
            within_24h = cnt
        else:
            older = cnt

    # Compute percentages (within_24h includes within_1h for the percentage)
    if total > 0:
        pct_1h = round((within_1h / total) * 100)
        pct_24h = round(((within_1h + within_24h) / total) * 100)
        pct_old = round((older / total) * 100)
    else:
        pct_1h = 0
        pct_24h = 0
        pct_old = 0

    return {
        "updated_within_1h": pct_1h,
        "updated_within_24h": pct_24h,
        "older_than_24h": pct_old,
        "total_entities": total,
    }
