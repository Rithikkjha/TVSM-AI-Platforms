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
import re
from typing import Any

from neo4j import AsyncGraphDatabase
from openai import AsyncAzureOpenAI

from config.settings import get_settings
from retrieval.search.ask_pipeline import ask_question as ask_monolithic
from retrieval.search.primitives import get_known_services, get_service_chain, search
from retrieval.search.query_classifier import ClassificationResult, QueryType, classify_query

logger = logging.getLogger(__name__)


def _is_list_all_services(question: str) -> bool:
    """True for 'list all services/repositories' style questions.

    Matches an enumeration verb (list/show/what/which/all/name) near a
    collection noun (services/repositories/repos/microservices/apps/systems),
    but NOT endpoint/api listings (those are per-service and handled
    elsewhere).
    """
    q = question.lower()
    if re.search(r"\b(endpoints?|apis?|routes?)\b", q):
        return False
    # Collection noun, usually plural (service -> prefer "services"). "service"
    # singular only counts with an explicit list/all cue to avoid matching
    # "what is X service".
    noun_plural = re.search(
        r"\b(services|repositor(?:y|ies)|repos|microservices|apps|applications|systems)\b",
        q,
    )
    noun_any = re.search(
        r"\b(services?|repositor(?:y|ies)|repos?|microservices?|apps?|applications?|systems?)\b",
        q,
    )
    # Enumeration cues
    list_cue = re.search(r"\b(list|show|name|all|every|which)\b", q)
    whatare_cue = re.search(r"\bwhat\s+(services|repos|repositories|systems|apps)\b", q)

    if list_cue and noun_any:
        return True
    if whatare_cue:
        return True
    # Bare plural noun with "are there" / "in the graph" style
    if noun_plural and re.search(r"\b(in the graph|are there|do we have|exist)\b", q):
        return True
    return False


def _new_driver() -> Any:
    from neo4j import AsyncGraphDatabase

    from config.settings import get_settings

    settings = get_settings()
    return AsyncGraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_user, settings.neo4j_password),
    )


async def _list_endpoints(service: str) -> list[dict[str, Any]]:
    """Open a Neo4j driver and return the service's EXPOSES endpoints."""
    from retrieval.search.repo_graph import list_service_endpoints

    driver = _new_driver()
    try:
        return await list_service_endpoints(driver, service)
    finally:
        await driver.close()


# Matches an HTTP method + path in a question, e.g. "request body of POST /bookings"
# or "/bookings/search request/response". Method is optional.
_ENDPOINT_RE = re.compile(
    r"\b(?:(GET|POST|PUT|PATCH|DELETE)\s+)?(/[A-Za-z0-9_\-/{}:.]+)",
    re.IGNORECASE,
)


async def _get_endpoint_detail(
    service: str, method: str | None, path: str
) -> list[dict[str, Any]]:
    """Fetch one endpoint's request/response schemas from the graph."""
    from retrieval.search.repo_graph import get_endpoint

    driver = _new_driver()
    try:
        return await get_endpoint(driver, method, path, service)
    finally:
        await driver.close()


def _fmt_fields(fields: Any) -> str:
    """Render a schema's field list as a small markdown table, or a note."""
    if not fields or not isinstance(fields, list):
        return "_No field-level schema captured._"
    lines = ["| Field | Type | Required |", "|-------|------|----------|"]
    for f in fields:
        if not isinstance(f, dict):
            continue
        name = f.get("name", "—")
        ftype = f.get("type", "—")
        req = "yes" if f.get("required") else "no"
        lines.append(f"| `{name}` | {ftype} | {req} |")
    return "\n".join(lines) if len(lines) > 2 else "_No field-level schema captured._"


# ---------------------------------------------------------------------------
# LLM prompts for different strategies
# ---------------------------------------------------------------------------

_SINGLE_SERVICE_PROMPT = """You are the TVS Engineering Memory Graph Assistant. You answer ONLY from the TVS engineering knowledge base, using ONLY the context provided in this request.

You are answering a question about a SPECIFIC service. All context provided is from that service's documentation.

RULES:
- Use ONLY the provided context. NEVER use outside or general world knowledge. No trivia, no arithmetic, no general facts.
- Answer from whatever relevant detail IS in the context. If some specific detail the user asked for is missing, answer what you can and state plainly which part is not in the retrieved context. Do NOT refuse outright when the context is about the right service.
- Provide ALL information from the context — full description, tech stack, endpoints, dependencies, configuration.
- Use markdown headings (## Overview, ## Tech Stack, ## API Endpoints, etc.) to organize.
- Render API endpoints as GFM pipe tables (Method / Endpoint / Description).
- Bold key terms. Use bullet points for lists.
- NEVER FABRICATE. If it's not in the context, say so.
- Cite ONLY chunks that directly support your statements using [ref:N] markers. Do not cite a chunk that does not support the answer.
"""

_FLOW_SYNTHESIS_PROMPT = """You are the TVS Engineering Memory Graph Assistant. You answer ONLY from the TVS engineering knowledge base, using ONLY the context provided. You are explaining a CROSS-SERVICE FLOW.

The user wants to understand how multiple services work together to accomplish a task. The context is organized by service, in dependency order.

RULES:
- Use ONLY the provided context. NEVER use outside or general world knowledge.
- Answer from whatever relevant detail IS in the context. If some integration detail is missing, state plainly which part is not documented rather than refusing outright.
- Structure your answer as a SEQUENCE showing what happens at each service.
- Include: what triggers the flow, what each service does (in order), what data passes between them.
- Generate a Mermaid sequence diagram showing the service interactions.
- Bold service names. Use numbered steps or a clear sequence.
- NEVER FABRICATE connections or APIs not mentioned in the context.
- Cite ONLY chunks that directly support your statements using [ref:N] markers.
- If the integration details between services are not documented, say so explicitly.
"""

_STRUCTURAL_TEMPLATE = """## {title}

{content}
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
    # Meta-intent allow-list (greetings / capability) → canned scope reply with
    # no retrieval and no citations. Keeps behaviour identical to the monolithic
    # path regardless of DEFAULT_ASK_MODE.
    from retrieval.search.scope_gate import META_REPLY, match_meta_intent

    if match_meta_intent(question):
        return {
            "answer": META_REPLY,
            "citations": [],
            "metadata": {"mode": "orchestrated", "query_type": "meta"},
        }

    # Get known services for classification
    try:
        known_services = await get_known_services()
    except Exception as exc:
        logger.warning("Failed to fetch known services, falling back to general: %s", exc)
        result = await ask_monolithic(question)
        result["metadata"] = {"mode": "orchestrated", "query_type": "general", "fallback_reason": "service_list_unavailable"}
        return result

    # "List all services / repositories" → answer from the complete graph list
    # (all known services), not similarity search which only returns a partial
    # set. Deterministic, exhaustive, no LLM.
    if _is_list_all_services(question):
        names = sorted(known_services)
        lines = [f"There are **{len(names)}** services in the knowledge graph:\n"]
        lines += [f"- {n}" for n in names]
        return {
            "answer": _STRUCTURAL_TEMPLATE.format(
                title="All services", content="\n".join(lines)
            ),
            "citations": [],
            "metadata": {
                "mode": "orchestrated",
                "query_type": "structural",
                "service_count": len(names),
            },
        }

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

    # Single-endpoint request/response → answer from the graph's stored schema
    # for that exact method+path. Triggered when the question names a path and
    # asks about request/response/body/payload/schema/params.
    wants_detail = any(
        w in q_lower
        for w in ["request", "response", "body", "payload", "schema", "params", "parameter"]
    )
    path_match = _ENDPOINT_RE.search(question)
    if wants_detail and path_match:
        method = (path_match.group(1) or "").upper() or None
        path = path_match.group(2)
        rows = await _get_endpoint_detail(service, method, path)
        if rows:
            r = rows[0]
            m = (r.get("method") or "").upper()
            p = r.get("path") or path
            parts = [f"### `{m} {p}`"]
            if r.get("auth"):
                parts.append(f"**Auth:** {r['auth']}")
            # Request
            req_name = r.get("request")
            parts.append(f"\n**Request body**{f' — `{req_name}`' if req_name else ''}:\n")
            parts.append(_fmt_fields(r.get("request_fields")))
            # Responses
            resp_schemas = r.get("response_schemas") or []
            if resp_schemas:
                for rs in resp_schemas:
                    if not isinstance(rs, dict):
                        continue
                    status = rs.get("status")
                    sname = rs.get("schema")
                    hdr = "**Response"
                    if status:
                        hdr += f" ({status})"
                    hdr += "**"
                    if sname:
                        hdr += f" — `{sname}`"
                    parts.append(f"\n{hdr}:\n")
                    parts.append(_fmt_fields(rs.get("fields")))
            else:
                parts.append("\n**Response:** _No response schema captured._")
            answer = "\n".join(parts)
            return {
                "answer": _STRUCTURAL_TEMPLATE.format(
                    title=f"{m} {p}", content=answer
                ),
                "citations": [],
                "metadata": {
                    "mode": "orchestrated",
                    "query_type": "structural",
                    "service": service,
                    "endpoint": f"{m} {p}",
                },
            }
        # Named a path but we couldn't resolve it → let normal search try.
        result = await ask_monolithic(question)
        result["metadata"] = {
            "mode": "orchestrated",
            "query_type": "structural",
            "service": service,
            "fallback_reason": "endpoint_not_resolved",
        }
        return result

    # Endpoint / API listing → answer directly from the graph (EXPOSES), which
    # is the authoritative, COMPLETE list. Vector retrieval only returns top-N
    # similar chunks, so it under-reports "list all endpoints"; the graph does
    # not. No LLM, no similarity cutoff.
    if any(w in q_lower for w in ["endpoint", "api", "apis", "routes", "route"]):
        endpoints = await _list_endpoints(service)
        if endpoints:
            lines = [f"**{service}** exposes {len(endpoints)} HTTP endpoint(s):\n"]
            lines.append("| Method | Path | Auth |")
            lines.append("|--------|------|------|")
            for e in endpoints:
                method = (e.get("method") or "").upper() or "—"
                path = e.get("path") or "—"
                auth = e.get("auth") or "—"
                lines.append(f"| {method} | `{path}` | {auth} |")
            answer = "\n".join(lines)
            title = f"Endpoints of {service}"
            return {
                "answer": _STRUCTURAL_TEMPLATE.format(title=title, content=answer),
                "citations": [],
                "metadata": {
                    "mode": "orchestrated",
                    "query_type": "structural",
                    "service": service,
                    "endpoint_count": len(endpoints),
                    "latency_note": "graph-only, no LLM",
                },
            }
        # No endpoints in the graph for this service → fall through to the
        # normal single-service search so the user still gets something.
        result = await ask_monolithic(question)
        result["metadata"] = {
            "mode": "orchestrated",
            "query_type": "structural",
            "service": service,
            "fallback_reason": "no_endpoints_in_graph",
        }
        return result

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
        # NOTE: no explicit temperature — GPT-5-family models (gpt-5.6-luna)
        # only accept the default temperature and reject other values.
        completion = await client.chat.completions.create(
            model=settings.azure_openai_deployment_gpt4o,
            messages=messages,
        )
        return completion.choices[0].message.content or ""
    finally:
        await client.close()


def _filter_used_citations(answer: str, citations: list[dict]) -> list[dict]:
    """Filter citations to only those actually referenced in the answer."""
    import re

    used_refs = set(int(m) for m in re.findall(r"\[ref:(\d+)\]", answer))
    return [c for c in citations if c["ref"] in used_refs]
