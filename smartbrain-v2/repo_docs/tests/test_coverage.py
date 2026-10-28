from __future__ import annotations

from repo_docs.coverage import gate_failures, ledger_gate


def _led(*pairs):
    return {"files": [{"path": p, "status": s} for p, s in pairs]}


def test_failed_missing_fails_gate():
    led = _led(("a.cs", "scanned"), ("gone.cs", "failed:missing"), ("x.lock", "skipped:lockfile"))
    g = ledger_gate(led)
    assert g["passes"] is False and g["failed"] == ["gone.cs"]
    assert gate_failures(led)[0] == "gone.cs (failed:missing)"


def test_all_scanned_or_skipped_passes():
    g = ledger_gate(_led(("a.cs", "scanned"), ("b.json", "scanned"), ("n/x.js", "skipped:vendor")))
    assert g["passes"] is True and g["scanned"] == ["a.cs", "b.json"]
    assert gate_failures(_led(("a.cs", "scanned"))) == []


def test_pending_fails_gate():
    led = _led(("a.cs", "pending"), ("b.json", "scanned"))
    g = ledger_gate(led)
    assert g["passes"] is False and g["pending"] == ["a.cs"]
    # option B: phase-2 extracted files pass without a phase-3 scan
    assert ledger_gate(_led(("c.json", "extracted"), ("d.cs", "scanned")))["passes"] is True
    assert gate_failures(_led(("c.json", "extracted"))) == []
