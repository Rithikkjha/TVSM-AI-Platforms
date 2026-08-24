"""Retry helper with exponential backoff for async callables.

The MCP orchestrator talks to remote servers (GitHub / Jira / Confluence
MCP servers) that may occasionally be slow, rate-limited, or unavailable.
Requirement 1.7 asks for basic exponential backoff (max 3 retries, base
2s) on those failures, logged appropriately. This module centralises
that behaviour as a reusable primitive so the orchestrator (and any
future ingestion component) can opt in without re-implementing the loop.

Design notes
------------

* **Opt-in, not mandatory.** :class:`MCPOrchestrator` accepts an
  optional :class:`RetryConfig`. When unset, calls go straight through
  — useful for unit tests that want deterministic timing and for the
  fake in-process clients that never fail.
* **Exception allow-list.** ``retry_on`` controls which exceptions
  trigger a retry; ``non_retryable`` short-circuits retries for
  known-permanent failures (auth errors, 4xx-style MCP responses).
  ``non_retryable`` wins over ``retry_on`` when both match.
* **Capped exponential delay.** The delay for attempt ``n`` is
  ``min(base_delay * 2 ** n, max_delay)`` with ``n`` starting at 0
  (first retry waits ``base_delay`` seconds by default). No jitter in
  V1 — keeping it deterministic makes the logs easier to read at the
  pilot scale.
* **Re-raise after exhaustion.** The *last* exception is re-raised
  once ``max_attempts`` is hit; the orchestrator's per-call
  ``except`` block then takes over as the final fallback so a dead
  source still doesn't halt the rest of the sync.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass(frozen=True)
class RetryConfig:
    """Configuration for :func:`with_retry`.

    Attributes:
        max_attempts: Total number of attempts (including the first
            call). Must be ``>= 1``. A value of ``1`` disables
            retries; a value of ``3`` matches the Requirement 1.7
            default (one initial call + two retries... or the spec's
            interpretation of "max 3 retries" as "up to 3 attempts").
        base_delay: Delay, in seconds, before the first retry.
            Subsequent retries double this up to ``max_delay``.
        max_delay: Upper bound (seconds) on the computed delay.
        retry_on: Exception classes that should trigger a retry. An
            exception matching both ``retry_on`` and ``non_retryable``
            will NOT be retried — ``non_retryable`` always wins.
        non_retryable: Exception classes that should immediately
            re-raise without retrying (e.g., auth errors).
    """

    max_attempts: int = 3
    base_delay: float = 2.0
    max_delay: float = 30.0
    retry_on: tuple[type[BaseException], ...] = (Exception,)
    non_retryable: tuple[type[BaseException], ...] = field(default_factory=tuple)


def _compute_delay(attempt: int, config: RetryConfig) -> float:
    """Return the capped exponential backoff delay for ``attempt`` (0-indexed).

    ``attempt == 0`` is the delay before the *first* retry (i.e. after
    the initial call failed). The formula is ``base_delay * 2 ** attempt``
    clamped to ``max_delay``. Kept pure so the unit tests can assert
    the schedule without mocking time.
    """

    delay = config.base_delay * (2**attempt)
    return float(min(delay, config.max_delay))


async def with_retry(
    func: Callable[..., Awaitable[T]],
    *args: Any,
    config: RetryConfig,
    **kwargs: Any,
) -> T:
    """Execute ``func(*args, **kwargs)`` with retry on failure.

    Parameters:
        func: An async callable returning an awaitable.
        *args: Positional arguments for ``func``.
        config: Retry policy. See :class:`RetryConfig`.
        **kwargs: Keyword arguments for ``func``.

    Returns:
        Whatever ``func`` returns on the first successful attempt.

    Raises:
        BaseException: The final exception raised by ``func`` if all
            attempts fail, or any exception matching ``config.non_retryable``.

    Behaviour:
        * On success, the result is returned immediately.
        * On a retryable exception, logs the attempt number, exception,
          and planned delay at WARNING, sleeps, then retries.
        * On an exception listed in ``non_retryable`` (or not in
          ``retry_on``), re-raises immediately without sleeping.
        * After exhausting ``max_attempts``, re-raises the last
          exception.
    """

    if config.max_attempts < 1:
        raise ValueError("RetryConfig.max_attempts must be >= 1")

    last_exc: BaseException | None = None

    for attempt in range(config.max_attempts):
        try:
            return await func(*args, **kwargs)
        except BaseException as exc:
            # non_retryable wins even if the exception is also in retry_on.
            if isinstance(exc, config.non_retryable):
                logger.warning(
                    "with_retry: non-retryable exception %s on attempt %d/%d; "
                    "re-raising without retry",
                    type(exc).__name__,
                    attempt + 1,
                    config.max_attempts,
                )
                raise
            if not isinstance(exc, config.retry_on):
                # Caller didn't ask to retry this kind of failure.
                raise

            last_exc = exc
            attempts_remaining = config.max_attempts - (attempt + 1)
            if attempts_remaining <= 0:
                logger.warning(
                    "with_retry: attempt %d/%d failed with %s: %s; "
                    "no attempts remaining, re-raising",
                    attempt + 1,
                    config.max_attempts,
                    type(exc).__name__,
                    exc,
                )
                raise

            delay = _compute_delay(attempt, config)
            logger.warning(
                "with_retry: attempt %d/%d failed with %s: %s; "
                "retrying in %.2fs",
                attempt + 1,
                config.max_attempts,
                type(exc).__name__,
                exc,
                delay,
            )
            await asyncio.sleep(delay)

    # Unreachable — the loop either returns, raises inside, or re-raises
    # on exhaustion. The assert keeps mypy happy about the return type.
    assert last_exc is not None  # noqa: S101
    raise last_exc


__all__ = ["RetryConfig", "with_retry"]
