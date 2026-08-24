"""Orchestrated query pipeline — classifies and routes questions.

This is the server-side orchestrator for the Web UI. It does what a smart MCP
agent (Kiro/Claude) would do manually: classify the question, call the right
primitives, and synthesize an answer.

Modes:
- "orchestrated" (this file): classify → route → strategy-specific retrieval → LLM
- "monolithic" (ask_pipeline.py): unchanged existing pipeline, always same path

The orchestrated mode handles 4 query types:
1. structural → graph-only, no LLM (~100ms)
2. single_service → filtered search + LLM (~2-3s)
3. cross_service_flow → chain + per-service search + flow LLM (~4-6s)
4. general → falls back to monolithic pipeline (~3-5s)
"""

from __future__ import annotations

import logging
from typing import Any

from neo4j import AsyncGraphDatabase
from openai import AsyncAzureOpenAI

from config.settings import get_settings
from retrieval.search.ask_pipeline import ask_question as ask_monolithic
from retrieval.search.primitives import get_known_services, get_service_chain, search
from retrieval.search.query_classifier import ClassificationResult, QueryType, classify_query

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# LLM prompts for different strategies
# ---------------------------------------------------------------------------

_SINGLE_SERVICE_PROMPT = """You are the Engineering Memory Graph Assistant. You have deep knowledge of this organization's engineering systems.

You are answering a question about a SPECIFIC service. All context provided is from that service's documentation.

RULES:
- Provide ALL information from the context — full description, tech stack, endpoints, dependencies, configuration.
- Use markdown headings (## Overview, ## Tech Stack, ## API Endpoints, etc.) to organize.
- Render API endpoints as GFM pipe tables (Method / Endpoint / Description).
- Bold key terms. Use bullet points for lists.
- NEVER FABRICATE. If it's not in the context, say so.
- Cite sources using [ref:N] markers.
"""

_FLOW_SYNTHESIS_PROMPT = """You are the Engineering Memory Graph Assistant. You are explaining a CROSS-SERVICE FLOW.

The user wants to understand how multiple services work together to accomplish a task. The context is organized by service, in dependency order.

RULES:
- Structure your answer as a SEQUENCE showing what happens at each service.
- Include: what triggers the flow, what each service does (in order), what data passes between them.
- Generate a Mermaid sequence diagram showing the service interactions.
- Bold service names. Use numbered steps or a clear sequence.
- NEVER FABRICATE connections or APIs not mentioned in the context.
- Cite sources using [ref:N] markers.
- If the integration details between services are not documented, say so explicitly.
"""

_STRUCTURAL_TEMPLATE = """## {title}

{content}

*Source: Graph traversal from Neo4j (no LLM synthesis — these are direct relationships stored in the knowledge graph).*
"""


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


async def ask_orchestrated(question: str) -> dict[str, Any]:
    """Answer a question using the orchestrated (routed) pipeline.

    Classifies the query, routes to the optimal strategy, and returns
    the answer with metadata about which path was taken.

    Args:
        question: The user's natural language question.

    Returns:
        Dict with keys: answer, citations, metadata.
    """
    # Get known services for classification
    try:
        known_services = await get_known_services()
    except Exception as exc:
        logger.warning("Failed to fetch known services, falling back to general: %s", exc)
        result = await ask_monolithic(question)
        result["metadata"] = {"mode": "orchestrated", "query_type": "general", "fallback_reason": "service_list_unavailable"}
        return result

    # Classify the query
    classification = classify_query(question, known_services)
    logger.info(
        "Query classified as %s (service: %s)",
        classification.query_type.value,
        classification.extracted_service,
    )

    # Route to strategy
    try:
        if classification.query_type == QueryType.STRUCTURAL:
            result = await _handle_structural(question, classification)
        elif classification.query_type == QueryType.SINGLE_SERVICE:
            result = await _handle_single_service(question, classification)
        elif classification.query_type == QueryType.CROSS_SERVICE_FLOW:
            result = await _handle_cross_service_flow(question, classification)
        else:
            result = await ask_monolithic(question)
            result["metadata"] = {"mode": "orchestrated", "query_type": "general"}
            return result
    except Exception as exc:
        # Any strategy failure → fall back to monolithic
        logger.warning(
            "Strategy %s failed, falling back to monolithic: %s",
            classification.query_type.value,
            exc,
        )
        result = await ask_monolithic(question)
        result["metadata"] = {
            "mode": "orchestrated",
            "query_type": "general",
            "fallback_reason": f"{classification.query_type.value}_strategy_failed",
        }
        return result

    return result


# ---------------------------------------------------------------------------
# Strategy: structural (graph-only, no LLM)
# ---------------------------------------------------------------------------


async def _handle_structural(
    question: str,
    classification: ClassificationResult,
) -> dict[str, Any]:
    """Handle structural questions with direct graph queries. No LLM needed."""
    service = classification.extracted_service
    if not service:
        # Can't identify service → fall back to monolithic
        result = await ask_monolithic(question)
        result["metadata"] = {"mode": "orchestrated", "query_type": "structural", "fallback_reason": "no_service_extracted"}
        return result

    q_lower = question.lower()

    # Determine what structural info they want
    if any(w in q_lower for w in ["depends on", "dependencies", "upstream", "uses", "calls"]):
        chain = await get_service_chain(service, direction="downstream", hops=2)
        if not chain:
            answer = f"No downstream dependencies found for **{service}** in the knowledge graph."
        else:
            lines = [f"**{service}** depends on {len(chain)} service(s):\n"]
            for item in chain:
                hop_label = f"(hop {item['hop_distance']})" if item["hop_distance"] > 1 else ""
                lines.append(f"- **{item['name']}** {hop_label}")
            answer = "\n".join(lines)
        title = f"Dependencies of {service}"

    elif any(w in q_lower for w in ["depend on this", "who uses", "blast radius", "impact", "downstream of", "what services use"]):
        chain = await get_service_chain(service, direction="upstream", hops=2)
        if not chain:
            answer = f"No services found that depend on **{service}** in the knowledge graph."
        else:
            lines = [f"**{len(chain)} service(s)** depend on {service}:\n"]
            for item in chain:
                hop_label = f"(hop {item['hop_distance']})" if item["hop_distance"] > 1 else ""
                lines.append(f"- **{item['name']}** {hop_label}")
            answer = "\n".join(lines)
        title = f"Impact / Blast Radius of {service}"

    else:
        # Generic structural — get both directions
        downstream = await get_service_chain(service, direction="downstream", hops=2)
        upstream = await get_service_chain(service, direction="upstream", hops=2)
        lines = [f"## {service} — Dependency Map\n"]
        if downstream:
            lines.append(f"**Depends on** ({len(downstream)}):")
            for item in downstream:
                lines.append(f"- {item['name']}")
        else:
            lines.append("**Depends on:** None found")
        lines.append("")
        if upstream:
            lines.append(f"**Depended on by** ({len(upstream)}):")
            for item in upstream:
                lines.append(f"- {item['name']}")
        else:
            lines.append("**Depended on by:** None found")
        answer = "\n".join(lines)
        title = f"Dependency Map of {service}"

    return {
        "answer": _STRUCTURAL_TEMPLATE.format(title=title, content=answer),
        "citations": [],
        "metadata": {
            "mode": "orchestrated",
            "query_type": "structural",
            "service": service,
            "latency_note": "graph-only, no LLM",
        },
    }


# ---------------------------------------------------------------------------
# Strategy: single_service (filtered search + LLM)
# ---------------------------------------------------------------------------


async def _handle_single_service(
    question: str,
    classification: ClassificationResult,
) -> dict[str, Any]:
    """Handle single-service questions with filtered retrieval."""
    service = classification.extracted_service
    if not service:
        result = await ask_monolithic(question)
        result["metadata"] = {"mode": "orchestrated", "query_type": "single_service", "fallback_reason": "no_service_extracted"}
        return result

    # Search only within this service's chunks
    chunks = await search(query=question, repo_filter=service, limit=5)

    if not chunks:
        # Fallback to monolithic if no chunks found for this service
        result = await ask_monolithic(question)
        result["metadata"] = {"mode": "orchestrated", "query_type": "single_service", "fallback_reason": "no_chunks_for_service"}
        return result

    # Build context with [ref:N] markers
    context_blocks = []
    citations = []
    for idx, chunk in enumerate(chunks, 1):
        section = chunk.get("section_title") or "Unknown Section"
        text = chunk.get("display_text") or chunk.get("text") or ""
        context_blocks.append(f"[ref:{idx}] Section: {section}\n{text}")
        citations.append({
            "ref": idx,
            "source_id": chunk.get("parent_source_id") or chunk.get("chunk_id"),
            "section_title": section,
            "source_ref": chunk.get("source_ref") or "",
            "url": None,
            "line_range": None,
        })

    context_text = "\n\n".join(context_blocks)

    # LLM synthesis
    answer = await _llm_synthesize(
        system_prompt=_SINGLE_SERVICE_PROMPT,
        context=context_text,
        question=question,
    )

    # Filter citations to only used ones
    used_citations = _filter_used_citations(answer, citations)

    return {
        "answer": answer,
        "citations": used_citations,
        "metadata": {
            "mode": "orchestrated",
            "query_type": "single_service",
            "service": service,
            "chunks_retrieved": len(chunks),
        },
    }


# ---------------------------------------------------------------------------
# Strategy: cross_service_flow (chain + per-service search + flow LLM)
# ---------------------------------------------------------------------------


async def _handle_cross_service_flow(
    question: str,
    classification: ClassificationResult,
) -> dict[str, Any]:
    """Handle cross-service flow questions with multi-service retrieval."""
    service = classification.extracted_service
    if not service:
        # Try monolithic for flow questions without a clear primary service
        result = await ask_monolithic(question)
        result["metadata"] = {"mode": "orchestrated", "query_type": "cross_service_flow", "fallback_reason": "no_service_extracted"}
        return result

    # Get the service chain
    chain = await get_service_chain(service, direction="downstream", hops=2)
    involved_services = [service] + [item["name"] for item in chain]

    # Cap at 5 services to bound latency
    involved_services = involved_services[:5]

    # Retrieve chunks per service
    context_blocks = []
    citations = []
    ref_counter = 0

    for svc in involved_services:
        svc_chunks = await search(query=question, repo_filter=svc, limit=2)
        if svc_chunks:
            for chunk in svc_chunks:
                ref_counter += 1
                section = chunk.get("section_title") or "Unknown"
                text = chunk.get("display_text") or chunk.get("text") or ""
                context_blocks.append(
                    f"[ref:{ref_counter}] Service: {svc} | Section: {section}\n{text}"
                )
                citations.append({
                    "ref": ref_counter,
                    "source_id": chunk.get("parent_source_id") or chunk.get("chunk_id"),
                    "section_title": f"{svc} — {section}",
                    "source_ref": chunk.get("source_ref") or "",
                    "url": None,
                    "line_range": None,
                })

    if not context_blocks:
        result = await ask_monolithic(question)
        result["metadata"] = {"mode": "orchestrated", "query_type": "cross_service_flow", "fallback_reason": "no_chunks_found"}
        return result

    # Add graph context about the chain
    chain_description = f"\n\n## Service Dependency Chain\n{service}"
    for item in chain:
        chain_description += f" → {item['name']}"

    context_text = "\n\n".join(context_blocks) + chain_description

    # LLM synthesis with flow-specific prompt
    answer = await _llm_synthesize(
        system_prompt=_FLOW_SYNTHESIS_PROMPT,
        context=context_text,
        question=question,
    )

    used_citations = _filter_used_citations(answer, citations)

    return {
        "answer": answer,
        "citations": used_citations,
        "metadata": {
            "mode": "orchestrated",
            "query_type": "cross_service_flow",
            "primary_service": service,
            "services_involved": involved_services,
            "chunks_retrieved": ref_counter,
        },
    }


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


async def _llm_synthesize(system_prompt: str, context: str, question: str) -> str:
    """Call GPT-4o with context and return the answer text."""
    import httpx

    settings = get_settings()
    client = AsyncAzureOpenAI(
        azure_endpoint=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_key,
        api_version=settings.azure_openai_api_version,
        http_client=httpx.AsyncClient(verify=False, timeout=60.0),
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"## Context\n\n{context}\n\n## Question\n\n{question}"},
    ]

    try:
        completion = await client.chat.completions.create(
            model=settings.azure_openai_deployment_gpt4o,
            messages=messages,
            temperature=0.1,
        )
        return completion.choices[0].message.content or ""
    finally:
        await client.close()


def _filter_used_citations(answer: str, citations: list[dict]) -> list[dict]:
    """Filter citations to only those actually referenced in the answer."""
    import re

    used_refs = set(int(m) for m in re.findall(r"\[ref:(\d+)\]", answer))
    return [c for c in citations if c["ref"] in used_refs]
