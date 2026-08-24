"""Per-source, per-stage ingestion counts for Clean_Ingest observability.

Requirement 15 asks for a structured report emitted at the end of a
``Clean_Ingest`` run so a developer can verify the run completed as expected
and diagnose gaps. The report is partitioned per ``Source_Type`` (the string
keys ``"steering"``, ``"confluence"``, ``"jira"``) and per pipeline stage:

* **chunking** — chunks created and chunks marked as duplicates by the
  Deduplication_Service (Req 15.1, 15.2).
* **deterministic extraction** — relationships produced by the
  Deterministic_Extractor (Req 15.3).
* **LLM enrichment** — LLM-inferred relationships bucketed by confidence
  ``high`` / ``medium`` / ``low`` (Req 15.4).

Design notes
------------

* **Counts only.** This module owns no pipeline logic — the orchestrator feeds
  it values it already computes (chunker output, ``DedupDecision`` markers,
  ``WriteResult.created_count`` on the deterministic write, and confidence
  buckets on the LLM results). Keeping it a passive accumulator makes it
  trivially testable and side-effect free.
* **Lazy per-source rows.** ``record_*`` methods use ``setdefault`` so a source
  row springs into existence on first write; there is no separate registration
  step and recording against an unseen source is never an error.
* **Skips are first-class.** A source whose Phase 1 branch failed or was
  unavailable (Req 12.6) is recorded via :meth:`IngestionReport.skip` and
  surfaced in :meth:`IngestionReport.render` so a gap is visible rather than
  silently absent.
"""

from __future__ import annotations

from dataclasses import dataclass, field

__all__ = ["SourceStageCounts", "IngestionReport"]


@dataclass
class SourceStageCounts:
    """Per-source, per-stage counts accumulated during a Clean_Ingest.

    All fields default to ``0`` so a freshly created row (e.g. via
    ``setdefault``) represents "nothing recorded yet".
    """

    chunks_created: int = 0
    duplicates_marked: int = 0
    deterministic_edges: int = 0
    llm_edges_high: int = 0
    llm_edges_medium: int = 0
    llm_edges_low: int = 0

    @property
    def llm_edges_total(self) -> int:
        """Sum of LLM-inferred edges across all confidence buckets."""
        return self.llm_edges_high + self.llm_edges_medium + self.llm_edges_low


@dataclass
class IngestionReport:
    """Structured per-source/per-stage report for a Clean_Ingest run (Req 15).

    ``per_source`` is keyed by ``Source_Type`` string (``"steering"``,
    ``"confluence"``, ``"jira"``). ``skipped_sources`` lists sources whose
    Phase 1 branch failed or was unavailable (Req 12.6).
    """

    per_source: dict[str, SourceStageCounts] = field(default_factory=dict)
    skipped_sources: list[str] = field(default_factory=list)

    def _counts_for(self, source: str) -> SourceStageCounts:
        """Return the counts row for ``source``, creating it lazily if absent."""
        return self.per_source.setdefault(source, SourceStageCounts())

    def record_chunks(self, source: str, created: int, duplicates: int) -> None:
        """Add chunk-creation and duplicate-marking counts for ``source`` (Req 15.1/15.2)."""
        counts = self._counts_for(source)
        counts.chunks_created += created
        counts.duplicates_marked += duplicates

    def record_deterministic(self, source: str, edges: int) -> None:
        """Add the count of deterministic-extractor relationships for ``source`` (Req 15.3)."""
        self._counts_for(source).deterministic_edges += edges

    def record_llm_edges(self, source: str, by_confidence: dict[str, int]) -> None:
        """Add LLM-inferred edge counts bucketed by confidence for ``source`` (Req 15.4).

        ``by_confidence`` maps confidence values (``"high"`` / ``"medium"`` /
        ``"low"``) to counts; unrecognized keys are ignored so malformed input
        never corrupts the totals.
        """
        counts = self._counts_for(source)
        counts.llm_edges_high += by_confidence.get("high", 0)
        counts.llm_edges_medium += by_confidence.get("medium", 0)
        counts.llm_edges_low += by_confidence.get("low", 0)

    def skip(self, source: str) -> None:
        """Record ``source`` as skipped (failed/unavailable Phase 1 branch, Req 12.6)."""
        if source not in self.skipped_sources:
            self.skipped_sources.append(source)

    def render(self) -> str:
        """Return a human-readable per-source/per-stage summary for the CLI log."""
        lines: list[str] = ["Ingestion report (per source, per stage):"]

        if not self.per_source:
            lines.append("  (no sources recorded)")

        for source in sorted(self.per_source):
            counts = self.per_source[source]
            lines.append(f"  {source}:")
            lines.append(f"    chunking: {counts.chunks_created} created, "
                         f"{counts.duplicates_marked} duplicates")
            lines.append(f"    deterministic: {counts.deterministic_edges} edges")
            lines.append(
                f"    llm: {counts.llm_edges_total} edges "
                f"(high={counts.llm_edges_high}, "
                f"medium={counts.llm_edges_medium}, "
                f"low={counts.llm_edges_low})"
            )

        if self.skipped_sources:
            skipped = ", ".join(sorted(self.skipped_sources))
            lines.append(f"  skipped sources: {skipped}")

        return "\n".join(lines)
