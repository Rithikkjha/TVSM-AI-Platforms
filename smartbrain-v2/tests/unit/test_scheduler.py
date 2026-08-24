"""Unit tests for :mod:`src.ingestion.scheduler`.

The scheduler is a thin asyncio wrapper around
:meth:`MCPOrchestrator.full_sync_all`. These tests use a fake
orchestrator (rather than mocking ``MCPOrchestrator`` itself) so the
assertions stay focused on the scheduler's own responsibilities:
lifecycle, periodicity, error isolation, and last-sync tracking.

``asyncio.sleep`` is patched module-by-module in the tests that need to
exercise multiple iterations — otherwise a 6-hour default would make
the test suite impractical. Because patching ``asyncio.sleep`` affects
the shared ``asyncio`` module globally, every test that needs to *also*
yield control (via ``sleep(0)``) captures the real sleep function
before patching and uses that for the short yields.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from unittest.mock import AsyncMock

import pytest
from config.settings import Settings
from processing.extraction.writer import WriteDecision, WriteResult
from ingestion.scheduler import PeriodicSyncScheduler, get_scheduler

# Captured once at import time so tests can always call the real
# ``asyncio.sleep`` even after monkeypatching scheduler's view of it.
_REAL_SLEEP = asyncio.sleep


class FakeOrchestrator:
    """In-process stand-in for :class:`MCPOrchestrator`.

    Tracks invocation count so tests can assert how many sync cycles
    ran, and supports per-call side effects (extra delay, raising) via
    ``side_effects`` — a list of tuples ``(result_or_exc, extra_delay)``.
    The scheduler only uses ``full_sync_all``; nothing else is stubbed.
    """

    def __init__(
        self,
        default_result: dict[str, WriteResult] | None = None,
    ) -> None:
        self.default_result = default_result or {}
        self.call_count = 0
        self.side_effects: list[tuple[object, float]] = []
        self.call_started = asyncio.Event()
        self.release_call = asyncio.Event()
        self.release_call.set()  # calls complete immediately by default

    async def full_sync_all(self) -> dict[str, WriteResult]:
        self.call_count += 1
        self.call_started.set()

        # Optional barrier for "long-running sync" tests.
        if not self.release_call.is_set():
            await self.release_call.wait()

        if self.side_effects:
            effect, delay = self.side_effects.pop(0)
            if delay > 0:
                await _REAL_SLEEP(delay)
            if isinstance(effect, BaseException):
                raise effect
            assert isinstance(effect, dict)
            return effect

        return dict(self.default_result)


def _write_result(created: int = 0, updated: int = 0, skipped: int = 0) -> WriteResult:
    """Build a :class:`WriteResult` with specific created/updated/skipped counts."""

    result = WriteResult()
    for i in range(created):
        result.entity_decisions[f"c{i}"] = WriteDecision.CREATED
    for i in range(updated):
        result.entity_decisions[f"u{i}"] = WriteDecision.UPDATED
    for i in range(skipped):
        result.entity_decisions[f"s{i}"] = WriteDecision.SKIPPED
    return result


def _patch_sleep(
    monkeypatch: pytest.MonkeyPatch,
    fake_long_sleep: Callable[[float], Awaitable[None]],
    short_threshold: float = 1.0,
) -> None:
    """Patch ``asyncio.sleep`` so short sleeps pass through and long ones are controlled.

    The scheduler's own interval sleep is very long (≥ 1 hour by
    default), so in practice every test-initiated ``await
    asyncio.sleep(0)`` falls below ``short_threshold`` and runs the
    captured real ``asyncio.sleep``. Only the scheduler's interval
    sleep is redirected to ``fake_long_sleep``.
    """

    async def router(seconds: float) -> None:
        if seconds < short_threshold:
            await _REAL_SLEEP(seconds)
            return
        await fake_long_sleep(seconds)

    monkeypatch.setattr("src.ingestion.scheduler.asyncio.sleep", router)


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------


class TestConstruction:
    def test_stores_interval_and_exposes_property(self) -> None:
        fake = FakeOrchestrator()
        scheduler = PeriodicSyncScheduler(fake, interval_hours=2.5)  # type: ignore[arg-type]
        assert scheduler.interval_hours == 2.5

    def test_last_sync_fields_default_to_none(self) -> None:
        fake = FakeOrchestrator()
        scheduler = PeriodicSyncScheduler(fake, interval_hours=6)  # type: ignore[arg-type]
        assert scheduler.last_sync_start is None
        assert scheduler.last_sync_end is None
        assert scheduler.last_sync_results is None

    def test_running_is_false_before_start(self) -> None:
        fake = FakeOrchestrator()
        scheduler = PeriodicSyncScheduler(fake, interval_hours=6)  # type: ignore[arg-type]
        assert scheduler.running is False

    @pytest.mark.parametrize("bad_interval", [0, -1, -0.5])
    def test_rejects_non_positive_interval(self, bad_interval: float) -> None:
        fake = FakeOrchestrator()
        with pytest.raises(ValueError):
            PeriodicSyncScheduler(fake, interval_hours=bad_interval)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# start / stop lifecycle
# ---------------------------------------------------------------------------


class TestLifecycle:
    async def test_start_launches_task_and_runs_first_sync(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        sleep_event = asyncio.Event()

        async def blocker(_seconds: float) -> None:
            await sleep_event.wait()

        _patch_sleep(monkeypatch, blocker)

        fake = FakeOrchestrator(default_result={"github:gh": _write_result(created=2)})
        scheduler = PeriodicSyncScheduler(fake, interval_hours=6)  # type: ignore[arg-type]

        await scheduler.start()
        await fake.call_started.wait()
        # Yield so _run_one_iteration finishes before we inspect state.
        for _ in range(10):
            if scheduler.last_sync_end is not None:
                break
            await asyncio.sleep(0)

        assert scheduler.running is True
        assert fake.call_count == 1

        sleep_event.set()
        await scheduler.stop()
        assert scheduler.running is False

    async def test_stop_without_start_is_noop(self) -> None:
        fake = FakeOrchestrator()
        scheduler = PeriodicSyncScheduler(fake, interval_hours=6)  # type: ignore[arg-type]
        await scheduler.stop()
        assert scheduler.running is False

    async def test_double_start_is_noop(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        sleep_event = asyncio.Event()

        async def blocker(_seconds: float) -> None:
            await sleep_event.wait()

        _patch_sleep(monkeypatch, blocker)

        fake = FakeOrchestrator()
        scheduler = PeriodicSyncScheduler(fake, interval_hours=6)  # type: ignore[arg-type]

        await scheduler.start()
        first_task = scheduler._task  # noqa: SLF001

        with caplog.at_level(logging.WARNING, logger="src.ingestion.scheduler"):
            await scheduler.start()

        assert scheduler._task is first_task  # noqa: SLF001
        assert any(
            "already running" in rec.message for rec in caplog.records
        )

        sleep_event.set()
        await scheduler.stop()

    async def test_async_context_manager_starts_and_stops(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        sleep_event = asyncio.Event()

        async def blocker(_seconds: float) -> None:
            await sleep_event.wait()

        _patch_sleep(monkeypatch, blocker)

        fake = FakeOrchestrator()
        async with PeriodicSyncScheduler(fake, interval_hours=6) as scheduler:  # type: ignore[arg-type]
            await fake.call_started.wait()
            assert scheduler.running is True
            sleep_event.set()

        assert scheduler.running is False
        assert fake.call_count >= 1


# ---------------------------------------------------------------------------
# Periodicity
# ---------------------------------------------------------------------------


class TestPeriodicity:
    async def test_sleeps_for_configured_interval_between_syncs(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        sleep_calls: list[float] = []
        max_sleeps = 3
        blocker = asyncio.Event()

        async def recording_blocker(seconds: float) -> None:
            sleep_calls.append(seconds)
            if len(sleep_calls) >= max_sleeps:
                await blocker.wait()
            else:
                # Yield so the test task can observe progress.
                await _REAL_SLEEP(0)

        _patch_sleep(monkeypatch, recording_blocker)

        fake = FakeOrchestrator()
        scheduler = PeriodicSyncScheduler(fake, interval_hours=2)  # type: ignore[arg-type]

        await scheduler.start()
        for _ in range(500):
            if len(sleep_calls) >= max_sleeps:
                break
            await asyncio.sleep(0)

        assert len(sleep_calls) >= max_sleeps
        # 2h → 7200s
        assert all(s == pytest.approx(7200.0) for s in sleep_calls[:max_sleeps])
        assert fake.call_count >= max_sleeps

        blocker.set()
        await scheduler.stop()

    async def test_calls_full_sync_all_repeatedly(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        iterations_done = asyncio.Semaphore(0)

        async def passthrough_sleep(_seconds: float) -> None:
            iterations_done.release()
            # Yield control so the test task can observe the release
            # and so the loop doesn't starve out other coroutines.
            await _REAL_SLEEP(0)

        _patch_sleep(monkeypatch, passthrough_sleep)

        fake = FakeOrchestrator()
        scheduler = PeriodicSyncScheduler(fake, interval_hours=6)  # type: ignore[arg-type]

        await scheduler.start()
        for _ in range(4):
            await iterations_done.acquire()

        await scheduler.stop()
        assert fake.call_count >= 4


# ---------------------------------------------------------------------------
# Last-sync tracking
# ---------------------------------------------------------------------------


class TestLastSyncTracking:
    async def test_tracks_start_end_and_results(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        sleep_event = asyncio.Event()

        async def blocker(_seconds: float) -> None:
            await sleep_event.wait()

        _patch_sleep(monkeypatch, blocker)

        expected_results = {
            "github:gh": _write_result(created=3, updated=1),
            "jira:jira": _write_result(updated=2, skipped=5),
        }
        fake = FakeOrchestrator(default_result=expected_results)
        scheduler = PeriodicSyncScheduler(fake, interval_hours=6)  # type: ignore[arg-type]

        await scheduler.start()
        await fake.call_started.wait()
        for _ in range(20):
            if scheduler.last_sync_end is not None:
                break
            await asyncio.sleep(0)

        assert scheduler.last_sync_start is not None
        assert scheduler.last_sync_end is not None
        assert scheduler.last_sync_end >= scheduler.last_sync_start
        assert scheduler.last_sync_results == expected_results

        sleep_event.set()
        await scheduler.stop()

    async def test_results_preserved_across_failed_iteration(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        iterations = asyncio.Semaphore(0)

        async def passthrough_sleep(_seconds: float) -> None:
            iterations.release()
            await _REAL_SLEEP(0)

        _patch_sleep(monkeypatch, passthrough_sleep)

        success_results = {"github:gh": _write_result(created=1)}
        fake = FakeOrchestrator()
        fake.side_effects = [
            (success_results, 0.0),
            (RuntimeError("transient boom"), 0.0),
        ]
        scheduler = PeriodicSyncScheduler(fake, interval_hours=6)  # type: ignore[arg-type]

        await scheduler.start()
        await iterations.acquire()  # after 1st iteration (success)
        await iterations.acquire()  # after 2nd iteration (failure)

        # Success snapshot survives the failure.
        assert scheduler.last_sync_results == success_results
        assert scheduler.last_sync_start is not None
        assert scheduler.last_sync_end is not None

        await scheduler.stop()


# ---------------------------------------------------------------------------
# Error isolation
# ---------------------------------------------------------------------------


class TestErrorIsolation:
    async def test_exception_does_not_kill_scheduler(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        iterations = asyncio.Semaphore(0)

        async def passthrough_sleep(_seconds: float) -> None:
            iterations.release()
            await _REAL_SLEEP(0)

        _patch_sleep(monkeypatch, passthrough_sleep)

        fake = FakeOrchestrator(default_result={"ok": _write_result(created=1)})
        fake.side_effects = [
            (RuntimeError("kaboom"), 0.0),
            ({"ok": _write_result(created=2)}, 0.0),
        ]
        scheduler = PeriodicSyncScheduler(fake, interval_hours=6)  # type: ignore[arg-type]

        with caplog.at_level(logging.ERROR, logger="src.ingestion.scheduler"):
            await scheduler.start()
            await iterations.acquire()  # failing iteration done
            await iterations.acquire()  # recovery iteration done
            await scheduler.stop()

        assert fake.call_count >= 2
        assert any("iteration failed" in rec.message for rec in caplog.records)

    async def test_multiple_exceptions_in_a_row_still_recover(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        iterations = asyncio.Semaphore(0)

        async def passthrough_sleep(_seconds: float) -> None:
            iterations.release()
            await _REAL_SLEEP(0)

        _patch_sleep(monkeypatch, passthrough_sleep)

        fake = FakeOrchestrator(default_result={"ok": _write_result(created=1)})
        fake.side_effects = [
            (RuntimeError("boom1"), 0.0),
            (ValueError("boom2"), 0.0),
            (RuntimeError("boom3"), 0.0),
            ({"ok": _write_result(created=5)}, 0.0),
        ]
        scheduler = PeriodicSyncScheduler(fake, interval_hours=6)  # type: ignore[arg-type]

        await scheduler.start()
        for _ in range(4):
            await iterations.acquire()
        await scheduler.stop()

        assert fake.call_count >= 4
        # Final successful iteration's results are exposed.
        assert scheduler.last_sync_results == {"ok": _write_result(created=5)}


# ---------------------------------------------------------------------------
# Graceful cancellation
# ---------------------------------------------------------------------------


class TestCancellation:
    async def test_stop_cancels_running_sync(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _patch_sleep(monkeypatch, AsyncMock())

        fake = FakeOrchestrator()
        fake.release_call.clear()  # full_sync_all blocks until released

        scheduler = PeriodicSyncScheduler(fake, interval_hours=6)  # type: ignore[arg-type]
        await scheduler.start()
        await fake.call_started.wait()

        # full_sync_all is blocked inside fake; stop() must cancel it.
        await scheduler.stop()

        assert scheduler.running is False
        assert scheduler.last_sync_start is not None
        # full_sync_all never returned, so results stayed at None.
        assert scheduler.last_sync_results is None

    async def test_stop_cancels_task_during_sleep(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        sleep_entered = asyncio.Event()

        async def blocker(_seconds: float) -> None:
            sleep_entered.set()
            # Simulate an indefinite wait until cancelled.
            await asyncio.Event().wait()

        _patch_sleep(monkeypatch, blocker)

        fake = FakeOrchestrator()
        scheduler = PeriodicSyncScheduler(fake, interval_hours=6)  # type: ignore[arg-type]

        await scheduler.start()
        await sleep_entered.wait()

        await scheduler.stop()

        assert scheduler.running is False
        assert fake.call_count == 1


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


class TestGetScheduler:
    def test_uses_settings_interval(self) -> None:
        settings = Settings(full_sync_interval_hours=12)
        fake = FakeOrchestrator()
        scheduler = get_scheduler(settings, fake)  # type: ignore[arg-type]
        assert scheduler.interval_hours == 12.0
        assert isinstance(scheduler, PeriodicSyncScheduler)

    def test_default_settings_interval(self) -> None:
        settings = Settings()
        fake = FakeOrchestrator()
        scheduler = get_scheduler(settings, fake)  # type: ignore[arg-type]
        # Default per requirements: every 6 hours.
        assert scheduler.interval_hours == 6.0
