"""Shared pytest fixtures and test isolation helpers."""

import pytest


@pytest.fixture(autouse=True)
def _reset_allowlist_cache():
    """Reset the auth middleware's module-level allowlist cache before and after
    every test.

    The allowlist cache (``app.middleware.auth._allowlist_cache``) is a
    process-global populated on first lookup. Without a reset, a test that
    primes the cache leaks it into later tests, which then read stale rows
    instead of their own mocked SharePoint data. This caused order-dependent
    failures in ``TestCheckAllowlist`` (e.g. the empty-allowlist / unavailable
    cases). Clearing the cache around each test keeps them independent.
    """
    import app.middleware.auth as auth_mod

    auth_mod.invalidate_allowlist_cache()
    yield
    auth_mod.invalidate_allowlist_cache()


@pytest.fixture(autouse=True)
def _reset_mpcp_tracker_state():
    """Reset the MPCP tracker service's module-level state between tests.

    The tracker service caches the whole hierarchy in module-level dicts plus
    the ``_loaded`` / ``_load_ok`` flags. These leak across tests: one test's
    failed-load (``_load_ok = False``) or seeded projects can change the
    behavior of a later, unrelated test — e.g. making a budget/dependency
    persist raise instead of succeed. Snapshotting and restoring the flags
    keeps tests independent without touching production behavior.
    """
    import app.services.mpcp_tracker_service as tracker_mod

    saved_loaded = getattr(tracker_mod, "_loaded", False)
    saved_load_ok = getattr(tracker_mod, "_load_ok", False)
    yield
    tracker_mod._loaded = saved_loaded
    tracker_mod._load_ok = saved_load_ok
