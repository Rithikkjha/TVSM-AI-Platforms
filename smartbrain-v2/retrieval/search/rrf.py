"""Pure Reciprocal Rank Fusion (RRF) for hybrid retrieval.

RRF merges multiple ranked lists (e.g. a dense vector ranking and a BM25
sparse ranking) into a single ranking by summing ``1 / (k + rank)`` for each
id across all lists. It requires no score normalization, which makes it robust
across rankings whose raw scores live on incomparable scales.

Rank convention
---------------
This implementation uses **1-based ranks**: the first (best) item in each list
has ``rank = 1`` and contributes ``1 / (k + 1)``, the second contributes
``1 / (k + 2)``, and so on. This matches the classic Cormack et al. RRF
formula ``1 / (k + rank)`` with ``rank >= 1`` and the ``k=60`` constant adopted
by Elasticsearch and Azure AI Search hybrid search.

The function is pure and deterministic: it performs no I/O and always returns
the same output for the same input. Ties in fused score are broken by
``chunk_id`` ascending so the ordering is fully deterministic.

Requirements: 3.3, 3.4
"""

from __future__ import annotations

__all__ = ["reciprocal_rank_fusion"]


def reciprocal_rank_fusion(
    ranked_lists: list[list[str]],
    k: int = 60,
    limit: int = 30,
) -> list[tuple[str, float]]:
    """Fuse ranked lists of chunk ids into a single ranking via RRF.

    For each ranked list, the id at 0-based position ``i`` is treated as having
    ``rank = i + 1`` (1-based) and contributes ``1 / (k + rank)`` to its fused
    score. Contributions are summed across all lists for each unique id.

    Args:
        ranked_lists: A list of ranked lists, where each inner list is an
            ordered sequence of chunk ids (best first). Within a single list,
            only the first occurrence of a given id counts toward the score.
        k: The RRF constant. Defaults to 60 (Requirement 3.3).
        limit: The maximum number of results to return. Defaults to 30.

    Returns:
        A list of ``(chunk_id, fused_score)`` tuples ordered by descending
        fused score, with ``chunk_id`` ascending as a deterministic tiebreak.
        The length is ``min(limit, number of unique ids)``.
    """

    fused_scores: dict[str, float] = {}

    for ranked_list in ranked_lists:
        seen_in_list: set[str] = set()
        for position, chunk_id in enumerate(ranked_list):
            # Only the first occurrence of an id within a single list counts,
            # so a duplicated id in one ranking cannot inflate its own score.
            if chunk_id in seen_in_list:
                continue
            seen_in_list.add(chunk_id)

            rank = position + 1  # 1-based rank
            fused_scores[chunk_id] = fused_scores.get(chunk_id, 0.0) + 1.0 / (k + rank)

    # Sort by descending fused score, breaking ties by chunk_id ascending.
    ordered = sorted(fused_scores.items(), key=lambda item: (-item[1], item[0]))

    return ordered[:limit]
