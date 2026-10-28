"""Ledger coverage gate. Phase 6 check 1 (docs/PIPELINE.md) calls this.

Option B (Phase 3 = targeted gap-fill): Phase 2 settles a file (``extracted``) or leaves it
``pending`` and lists it in gaps.json; the Phase 3 agent marks the gap files it resolved
``scanned``. The gate passes when every non-skipped file is ``extracted`` or ``scanned``. Any
``failed:*`` entry (including ``failed:missing``) and any remaining ``pending`` file fail it.
"""

from __future__ import annotations


def ledger_gate(ledger: dict) -> dict:
    """Bucket ledger paths by status and decide whether the ledger passes the gate."""
    failed, pending, extracted, scanned = [], [], [], []
    for f in ledger.get("files") or []:
        st = f.get("status") or ""
        if st.startswith("failed:"):
            failed.append(f["path"])
        elif st == "pending":
            pending.append(f["path"])
        elif st == "extracted":
            extracted.append(f["path"])
        elif st == "scanned":
            scanned.append(f["path"])
    return {
        "failed": sorted(failed), "pending": sorted(pending),
        "extracted": sorted(extracted), "scanned": sorted(scanned),
        "passes": not failed and not pending,
    }


def gate_failures(ledger: dict) -> list[str]:
    """Human-readable gate failure reasons; ``failed:*`` entries are listed first."""
    status = {f["path"]: f.get("status") for f in ledger.get("files") or []}
    g = ledger_gate(ledger)
    out = [f"{p} ({status[p]})" for p in g["failed"]]
    out += [f"{p} (pending: not extracted by phase 2, not resolved by phase 3)"
            for p in g["pending"]]
    return out
