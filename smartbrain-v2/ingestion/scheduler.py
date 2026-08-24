"""Background scheduler for periodic full syncs.

Requirement 1.5 asks the MCP_Orchestrator to perform a full
re-synchronization across every registered source at a configurable
interval (default: every 6 hours). The webhook path covers near-real-time
updates; the scheduler exists to catch anything the webhooks missed — a
dropped delivery, a newly-added repo the webhook provider doesn't know
about yet, or a silent source-side edit that never emits a notification.

Design notes
------------

* **Single asyncio background task.** The scheduler owns one
  :class:`asyncio.Task` running :meth:`PeriodicSyncScheduler._run`. It is
  created lazily by :meth:`start` and cancelled by :meth:`stop`. No
  thread pools, no subprocesses — the whole FastAPI app runs on a single
  event loop at V1 scale, and co-locating the scheduler there keeps
  lifecycle management simple.
* **Two exit paths that must compose.** ``stop()`` sets ``_stopped``
  *and* cancels the task. The flag handles the "exit at the top of the
  next iteration" case (e.g. if we're between iterations); the
  cancellation interrupts an in-flight ``asyncio.sleep`` or a
  long-running ``full_sync_all``. Either way the scheduler exits cleanly
  — callers always see a fully-stopped scheduler after :meth:`stop`
  returns.
* **Exceptions never kill the scheduler.** Each iteration is wrapped in
  ``try/except Exception`` so a transient failure (Neo4j blip, MCP
  server unreachable) only costs one cycle. The scheduler logs and
  sleeps normally before the next attempt. ``asyncio.CancelledError`` is
  explicitly *not* caught at the iteration boundary — it must propagate
  so :meth:`stop` can tear the task down.
* **Last-sync observability.** ``last_sync_start`` /
  ``last_sync_end`` / ``last_sync_results`` are plain public
  attributes, updated on every iteration. The /health endpoint (built
  in a later task) will expose them directly. ``last_sync_results`` is
  only written on a successful sync so a single failure doesn't wipe
  out the last good snapshot.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime
from types import TracebackType
from typing import Self

from config.settings import Settings
from processing.extraction.writer import WriteResult
from ingestion.orchestrator import MCPOrchestrator

logger = logging.getLogger(__name__)


class PeriodicSyncScheduler:
    """Run :meth:`MCPOrchestrator.full_sync_all` on a fixed cadence.

    Typical usage::

        scheduler = PeriodicSyncScheduler(orchestrator, interval_hours=6)
        await scheduler.start()
        try:
            # ... app runs ...
        finally:
            await scheduler.stop()

    Or as an async context manager::

        async with PeriodicSyncScheduler(orchestrator, interval_hours=6):
            # ... app runs ...
    """

    def __init__(
        self,
        orchestrator: MCPOrchestrator,
        interval_hours: float,
    ) -> None:
        if interval_hours <= 0:
            raise ValueError(
                f"interval_hours must be > 0, got {interval_hours!r}"
            )
        self._orchestrator = orchestrator
        self._interval_hours = float(interval_hours)
        self._interval_seconds = self._interval_hours * 3600.0
        self._stopped = False
        self._task: asyncio.Task[None] | None = None

        # Observable state consumed by the /health endpoint.
        self.last_sync_start: datetime | None = None
        self.last_sync_end: datetime | None = None
        self.last_sync_results: dict[str, WriteResult] | None = None

    # -- introspection ---------------------------------------------------

    @property
    def running(self) -> bool:
        """Return ``True`` while the background task is active."""

        return self._task is not None and not self._task.done()

    @property
    def interval_hours(self) -> float:
        """The configured interval in hours. Useful for the /health response."""

        return self._interval_hours

    # -- lifecycle -------------------------------------------------------

    async def start(self) -> None:
        """Launch the background sync task.

        Calling :meth:`start` twice without an intervening :meth:`stop`
        is a no-op (logged at WARNING) — the scheduler owns exactly one
        task at a time.
        """

        if self._task is not None and not self._task.done():
            logger.warning(
                "PeriodicSyncScheduler.start called while a task is already running"
            )
            return

        self._stopped = False
        self._task = asyncio.create_task(
            self._run(), name="periodic-sync-scheduler"
        )
        logger.info(
            "PeriodicSyncScheduler started (interval=%.2fh)", self._interval_hours
        )

    async def stop(self) -> None:
        """Signal the scheduler to stop and await task completion.

        Safe to call multiple times and safe to call when :meth:`start`
        was never invoked. Any exception raised from the cancelled task
        other than :class:`asyncio.CancelledError` is logged but not
        re-raised — ``stop`` is expected to always succeed from the
        caller's perspective.
        """

        self._stopped = True
        task = self._task
        if task is None:
            return

        if not task.done():
            task.cancel()

        try:
            await task
        except asyncio.CancelledError:
            # Expected: we just cancelled it.
            pass
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning(
                "PeriodicSyncScheduler task raised during shutdown: %s", exc
            )
        finally:
            self._task = None

        logger.info("PeriodicSyncScheduler stopped")

    async def __aenter__(self) -> Self:
        await self.start()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        await self.stop()

    # -- internals -------------------------------------------------------

    async def _run(self) -> None:
        """Main loop — one iteration + one sleep per cycle.

        The try/except around ``_run_one_iteration`` is what guarantees
        an unexpected error doesn't kill the scheduler (Requirement
        1.5). ``asyncio.CancelledError`` is deliberately not caught
        here — the outer handler re-raises it so :meth:`stop` sees the
        task finish cleanly.
        """

        logger.debug(
            "PeriodicSyncScheduler loop entering; interval_seconds=%.2f",
            self._interval_seconds,
        )
        try:
            while not self._stopped:
                try:
                    await self._run_one_iteration()
                except asyncio.CancelledError:
                    raise
                except Exception:
                    # Full traceback captured via logger.exception so
                    # operators can diagnose without needing to re-run.
                    logger.exception(
                        "PeriodicSyncScheduler: iteration failed unexpectedly; "
                        "will retry after the normal interval"
                    )

                if self._stopped:
                    break

                try:
                    await asyncio.sleep(self._interval_seconds)
                except asyncio.CancelledError:
                    raise
        except asyncio.CancelledError:
            logger.info("PeriodicSyncScheduler loop cancelled")
            raise
        finally:
            logger.debug("PeriodicSyncScheduler loop exited")

    async def _run_one_iteration(self) -> None:
        """Run a single ``full_sync_all`` cycle and record timing.

        Updates ``last_sync_start`` and ``last_sync_end`` unconditionally
        (both on success and failure) so the /health endpoint can
        distinguish "hasn't run yet" (``None``) from "ran at T but
        didn't produce results" (``last_sync_end`` set,
        ``last_sync_results`` unchanged). ``last_sync_results`` is only
        overwritten on success so the previous good snapshot survives a
        transient failure.
        """

        start_time = datetime.now(UTC)
        self.last_sync_start = start_time
        logger.info(
            "PeriodicSyncScheduler: full sync starting at %s",
            start_time.isoformat(),
        )

        try:
            results = await self._orchestrator.full_sync_all()
        except asyncio.CancelledError:
            # Record the end time so observers can see the truncated
            # run, then let the cancellation propagate.
            self.last_sync_end = datetime.now(UTC)
            raise
        except Exception:
            self.last_sync_end = datetime.now(UTC)
            raise

        end_time = datetime.now(UTC)
        self.last_sync_end = end_time
        self.last_sync_results = results

        duration_s = (end_time - start_time).total_seconds()
        created = sum(r.created_count for r in results.values())
        updated = sum(r.updated_count for r in results.values())
        skipped = sum(r.skipped_count for r in results.values())
        embedding_failures = sum(
            len(r.embedding_failures) for r in results.values()
        )
        logger.info(
            "PeriodicSyncScheduler: full sync complete at %s "
            "(duration=%.2fs, clients=%d, created=%d, updated=%d, "
            "skipped=%d, embedding_failures=%d)",
            end_time.isoformat(),
            duration_s,
            len(results),
            created,
            updated,
            skipped,
            embedding_failures,
        )


def get_scheduler(
    settings: Settings,
    orchestrator: MCPOrchestrator,
) -> PeriodicSyncScheduler:
    """Construct a :class:`PeriodicSyncScheduler` from application settings.

    Uses ``settings.full_sync_interval_hours`` (default 6) as the cadence.
    Kept as a factory so the FastAPI startup path has a single,
    dependency-injection-friendly entry point.
    """

    return PeriodicSyncScheduler(
        orchestrator=orchestrator,
        interval_hours=float(settings.full_sync_interval_hours),
    )


__all__ = [
    "PeriodicSyncScheduler",
    "get_scheduler",
]
