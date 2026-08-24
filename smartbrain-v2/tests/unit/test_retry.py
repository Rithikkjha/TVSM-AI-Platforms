"""Unit tests for :mod:`src.ingestion.retry`.

Covers the four behaviours the orchestrator relies on:

1. Successful calls bypass the retry loop (no sleep, no extra calls).
2. Retryable failures fire exponential backoff and eventually re-raise
   once ``max_attempts`` is exhausted.
3. Exceptions listed in ``non_retryable`` short-circuit the loop.
4. The delay schedule is ``base * 2 ** attempt`` capped at ``max_delay``.

``asyncio.sleep`` is patched so the suite stays fast and deterministic
while still asserting the schedule the retry loop asks for.
"""

from __future__ import annotations

import logging
from typing import Any
from unittest.mock import AsyncMock

import pytest
from ingestion.retry import RetryConfig, _compute_delay, with_retry


class TestComputeDelay:
    """Exponential backoff schedule computation."""

    def test_first_retry_is_base_delay(self) -> None:
        config = RetryConfig(base_delay=2.0, max_delay=30.0)
        assert _compute_delay(0, config) == 2.0

    def test_second_retry_doubles(self) -> None:
        config = RetryConfig(base_delay=2.0, max_delay=30.0)
        assert _compute_delay(1, config) == 4.0

    def test_schedule_is_capped_at_max_delay(self) -> None:
        config = RetryConfig(base_delay=2.0, max_delay=5.0)
        # 2 * 2^3 == 16, clamped to 5.
        assert _compute_delay(3, config) == 5.0
        # 2 * 2^10 == 2048, still clamped to 5.
        assert _compute_delay(10, config) == 5.0


class TestWithRetrySuccess:
    async def test_first_attempt_success_returns_value(self) -> None:
        func = AsyncMock(return_value="ok")
        config = RetryConfig()
        result = await with_retry(func, "arg1", config=config, key="value")
        assert result == "ok"
        func.assert_awaited_once_with("arg1", key="value")

    async def test_first_attempt_success_does_not_sleep(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        sleep_mock = AsyncMock()
        monkeypatch.setattr("src.ingestion.retry.asyncio.sleep", sleep_mock)
        func = AsyncMock(return_value=42)
        await with_retry(func, config=RetryConfig())
        sleep_mock.assert_not_awaited()


class TestWithRetryRetryable:
    async def test_retries_on_failure_then_succeeds(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        sleep_mock = AsyncMock()
        monkeypatch.setattr("src.ingestion.retry.asyncio.sleep", sleep_mock)

        attempts = {"n": 0}

        async def flaky(*_args: Any, **_kwargs: Any) -> str:
            attempts["n"] += 1
            if attempts["n"] < 3:
                raise RuntimeError(f"transient {attempts['n']}")
            return "done"

        config = RetryConfig(max_attempts=3, base_delay=1.0, max_delay=8.0)
        result = await with_retry(flaky, config=config)

        assert result == "done"
        assert attempts["n"] == 3
        # Two retries, so two sleeps, with doubling delays.
        assert sleep_mock.await_count == 2
        delays = [call.args[0] for call in sleep_mock.await_args_list]
        assert delays == [1.0, 2.0]

    async def test_exponential_backoff_schedule(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        sleep_mock = AsyncMock()
        monkeypatch.setattr("src.ingestion.retry.asyncio.sleep", sleep_mock)

        async def always_fails(*_args: Any, **_kwargs: Any) -> str:
            raise RuntimeError("nope")

        config = RetryConfig(max_attempts=4, base_delay=2.0, max_delay=100.0)
        with pytest.raises(RuntimeError, match="nope"):
            await with_retry(always_fails, config=config)

        # 3 retries: delays = 2, 4, 8.
        delays = [call.args[0] for call in sleep_mock.await_args_list]
        assert delays == [2.0, 4.0, 8.0]

    async def test_delay_is_capped_at_max_delay(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        sleep_mock = AsyncMock()
        monkeypatch.setattr("src.ingestion.retry.asyncio.sleep", sleep_mock)

        async def always_fails(*_args: Any, **_kwargs: Any) -> None:
            raise RuntimeError("nope")

        # base_delay=10, max_delay=15 → raw schedule 10, 20, 40 ... clamped.
        config = RetryConfig(max_attempts=4, base_delay=10.0, max_delay=15.0)
        with pytest.raises(RuntimeError):
            await with_retry(always_fails, config=config)

        delays = [call.args[0] for call in sleep_mock.await_args_list]
        assert delays == [10.0, 15.0, 15.0]

    async def test_reraises_last_exception_after_max_attempts(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr("src.ingestion.retry.asyncio.sleep", AsyncMock())

        attempts = {"n": 0}

        async def always_fails(*_args: Any, **_kwargs: Any) -> None:
            attempts["n"] += 1
            raise RuntimeError(f"attempt {attempts['n']}")

        config = RetryConfig(max_attempts=3, base_delay=0.1, max_delay=1.0)
        with pytest.raises(RuntimeError, match="attempt 3"):
            await with_retry(always_fails, config=config)
        assert attempts["n"] == 3

    async def test_logs_each_retry(
        self,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        monkeypatch.setattr("src.ingestion.retry.asyncio.sleep", AsyncMock())

        attempts = {"n": 0}

        async def flaky(*_args: Any, **_kwargs: Any) -> str:
            attempts["n"] += 1
            if attempts["n"] < 2:
                raise RuntimeError("boom")
            return "ok"

        config = RetryConfig(max_attempts=3, base_delay=1.0, max_delay=1.0)
        with caplog.at_level(logging.WARNING, logger="src.ingestion.retry"):
            await with_retry(flaky, config=config)

        # At least one WARNING line describing the retry.
        assert any(
            "attempt 1/3" in record.message and "retrying" in record.message
            for record in caplog.records
        )


class TestWithRetryNonRetryable:
    async def test_non_retryable_exception_bypasses_retry(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        sleep_mock = AsyncMock()
        monkeypatch.setattr("src.ingestion.retry.asyncio.sleep", sleep_mock)

        attempts = {"n": 0}

        async def auth_failure(*_args: Any, **_kwargs: Any) -> None:
            attempts["n"] += 1
            raise PermissionError("bad token")

        config = RetryConfig(
            max_attempts=5,
            base_delay=1.0,
            max_delay=1.0,
            retry_on=(Exception,),
            non_retryable=(PermissionError,),
        )
        with pytest.raises(PermissionError, match="bad token"):
            await with_retry(auth_failure, config=config)

        # The function was invoked exactly once and never slept.
        assert attempts["n"] == 1
        sleep_mock.assert_not_awaited()

    async def test_exception_outside_retry_on_is_reraised(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        sleep_mock = AsyncMock()
        monkeypatch.setattr("src.ingestion.retry.asyncio.sleep", sleep_mock)

        attempts = {"n": 0}

        async def keyboard_interrupt(*_args: Any, **_kwargs: Any) -> None:
            attempts["n"] += 1
            raise KeyboardInterrupt

        config = RetryConfig(
            max_attempts=3,
            base_delay=1.0,
            max_delay=1.0,
            retry_on=(Exception,),
        )
        with pytest.raises(KeyboardInterrupt):
            await with_retry(keyboard_interrupt, config=config)
        assert attempts["n"] == 1
        sleep_mock.assert_not_awaited()


class TestWithRetryValidation:
    async def test_rejects_zero_max_attempts(self) -> None:
        async def anything(*_args: Any, **_kwargs: Any) -> None:
            return None

        config = RetryConfig(max_attempts=0)
        with pytest.raises(ValueError, match="max_attempts"):
            await with_retry(anything, config=config)
