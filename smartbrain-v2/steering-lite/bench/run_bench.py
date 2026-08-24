"""SWE Bench runner — evaluates 3 contenders: Full Brain vs Brain-Lite vs Steering Lite.

Contenders:
    1. Full Brain    — ask_question (vector search + graph + GPT answers internally)
    2. Brain-Lite    — search_graph + get_service_info + get_impact → bench LLM answers
    3. Steering Lite — list_services + search_services + get_service + get_dependencies → bench LLM answers

Usage:
    python steering-lite/bench/run_bench.py
    python steering-lite/bench/run_bench.py --difficulty easy
    python steering-lite/bench/run_bench.py --difficulty medium

Output:
    steering-lite/bench/results/bench_{timestamp}.md
    steering-lite/bench/results/bench_{timestamp}.json
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

QUESTIONS_FILE = Path("steering-lite/bench/questions.yaml")
RESULTS_DIR = Path("steering-lite/bench/results")

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


# ---------------------------------------------------------------------------
# Shared LLM call (used by Brain-Lite and Steering Lite)
# ---------------------------------------------------------------------------


async def _call_bench_llm(question: str, context: str) -> str:
    """Call LLM with assembled context to answer the question."""
    from dotenv import load_dotenv
    load_dotenv()

    import httpx
    from openai import AsyncAzureOpenAI
    from src.config.settings import get_settings

    settings = get_settings()
    client = AsyncAzureOpenAI(
        azure_endpoint=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_key,
        api_version=settings.azure_openai_api_version,
        http_client=httpx.AsyncClient(verify=False),
    )

    try:
        response = await client.chat.completions.create(
            model=settings.azure_openai_deployment_gpt4o,
            messages=[
                {"role": "system", "content": "You answer questions about engineering microservices using the provided context. Be detailed and specific. Include service names, endpoints, technologies. If the context doesn't have the info, say so."},
                {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"},
            ],
            temperature=0.1,
            max_tokens=2000,
        )
        return response.choices[0].message.content or ""
    except Exception as exc:
        return f"LLM Error: {exc}"
    finally:
        await client.close()


# ---------------------------------------------------------------------------
# Contender 1: FULL BRAIN (ask_question — self-contained GPT answer)
# ---------------------------------------------------------------------------


async def call_full_brain(question: str) -> dict[str, Any]:
    """Full Brain: calls ask_question which does vector search + graph + GPT internally."""
    from dotenv import load_dotenv
    load_dotenv()

    start = time.time()
    try:
        from src.mcp_server.tools.ask import ask_question
        result = await ask_question(question)
        elapsed = round(time.time() - start, 2)

        if isinstance(result, dict):
            answer = result.get("answer") or result.get("message") or result.get("error") or ""
        else:
            answer = str(result) if result else ""

        return {"answer": answer, "time": elapsed, "error": None}
    except Exception as exc:
        return {"answer": "", "time": round(time.time() - start, 2), "error": str(exc)}


# ---------------------------------------------------------------------------
# Contender 2: BRAIN-LITE (search_graph + get_service_info + get_impact → bench LLM)
# ---------------------------------------------------------------------------


async def call_brain_lite(question: str) -> dict[str, Any]:
    """Brain-Lite: uses vector search + Neo4j for context, bench LLM for answer."""
    from dotenv import load_dotenv
    load_dotenv()

    start = time.time()
    try:
        from src.mcp_server.tools.search import search_graph
        from src.mcp_server.tools.service_info import get_service_info
        from src.mcp_server.tools.impact import get_impact

        context_parts = []

        # 1. Vector search for relevant entities
        search_result = await search_graph(question, limit=5)
        if not search_result.get("error"):
            hits = search_result.get("results", [])
            context_parts.append(f"=== VECTOR SEARCH RESULTS ===\n{json.dumps(hits, indent=2)}")

            # 2. Get service info for top hits that look like services
            service_names = _extract_service_names_from_hits(hits)
            for svc_name in service_names[:3]:
                svc_info = await get_service_info(svc_name)
                if not svc_info.get("error"):
                    # Extract key fields including full content_summary (steering content)
                    service = svc_info.get("service", {})
                    docs = svc_info.get("documents", [])
                    upstream = svc_info.get("upstream_dependencies", [])
                    downstream = svc_info.get("downstream_dependents", [])
                    # Include content_summary which has the full steering text
                    content_summary = service.get("content_summary", "")
                    context_parts.append(
                        f"\n=== SERVICE: {svc_name} ===\n"
                        f"Description: {service.get('description', '')}\n"
                        f"Content: {content_summary[:3000]}\n"
                        f"Upstream deps: {json.dumps(upstream, default=str)[:500]}\n"
                        f"Downstream deps: {json.dumps(downstream, default=str)[:500]}\n"
                        f"Documents: {json.dumps([d.get('title') for d in docs], default=str)[:300]}"
                    )

            # 3. Get impact for the first service (if relevant to question)
            if service_names and any(w in question.lower() for w in ["impact", "break", "down", "affect", "depend"]):
                impact_result = await get_impact(service_names[0])
                if not impact_result.get("error"):
                    context_parts.append(f"\n=== IMPACT ANALYSIS: {service_names[0]} ===\n{json.dumps(impact_result, indent=2, default=str)[:1500]}")

        # Assemble context and call bench LLM
        context = "\n".join(context_parts)
        if len(context) > 16000:
            context = context[:16000] + "\n... [truncated]"

        answer = await _call_bench_llm(question, context)
        elapsed = round(time.time() - start, 2)
        return {"answer": answer, "time": elapsed, "error": None}
    except Exception as exc:
        return {"answer": "", "time": round(time.time() - start, 2), "error": str(exc)}


def _extract_service_names_from_hits(hits: list[dict]) -> list[str]:
    """Extract service names from vector search hits."""
    names = []
    for hit in hits:
        sid = hit.get("source_id", "")
        # source_id patterns: "service:booking-crud-services", "steering:tvsm-auth:tech"
        if sid.startswith("service:"):
            name = sid.replace("service:", "")
            if name not in names:
                names.append(name)
        elif sid.startswith("steering:"):
            parts = sid.replace("steering:", "").split(":")
            name = parts[0]
            if name not in names:
                names.append(name)
    return names


# ---------------------------------------------------------------------------
# Contender 3: STEERING LITE (file search + file read → bench LLM)
# ---------------------------------------------------------------------------


async def call_steering_lite(question: str) -> dict[str, Any]:
    """Steering Lite: reads full service files (like Kiro would), bench LLM answers."""
    import importlib.util

    start = time.time()
    try:
        spec = importlib.util.spec_from_file_location(
            "lite_server", "steering-lite/mcp_server/server.py"
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        context_parts = []

        # 1. Get index to find service names
        index = await mod.list_services()

        # 2. Extract service name from question (if mentioned directly)
        direct_names = _extract_service_name_from_question(question, index)

        # 3. If no direct name, search by keywords to find relevant services
        if not direct_names:
            keywords = _extract_keywords(question)
            search_results = []
            for kw in keywords[:3]:
                result = await mod.search_services(kw)
                if "Error" not in result and "No services" not in result:
                    search_results.append(result)
            direct_names = _extract_service_names_from_search(search_results)

        # 4. Get FULL service file(s) — no truncation, like Kiro would read them
        for svc_name in direct_names[:3]:
            full_content = await mod.get_service(svc_name)
            if "Error" not in full_content:
                context_parts.append(full_content)

        # 5. Always include full dependencies map
        deps = await mod.get_dependencies()
        context_parts.append(deps)

        # 6. If no services found, include the index for discovery
        if not direct_names:
            context_parts.insert(0, index)

        # Assemble — allow larger context since this is how real usage works
        context = "\n\n".join(context_parts)
        if len(context) > 30000:
            context = context[:30000] + "\n... [truncated]"

        answer = await _call_bench_llm(question, context)
        elapsed = round(time.time() - start, 2)
        return {"answer": answer, "time": elapsed, "error": None}
    except Exception as exc:
        return {"answer": "", "time": round(time.time() - start, 2), "error": str(exc)}


def _extract_keywords(question: str) -> list[str]:
    """Extract search keywords from a question."""
    stopwords = {"what", "which", "how", "does", "the", "is", "are", "our", "all",
                 "would", "be", "if", "we", "need", "to", "a", "an", "for", "from",
                 "with", "that", "this", "of", "in", "on", "and", "or", "do", "can",
                 "services", "service", "use", "using", "about", "tell", "me", "list"}
    words = question.lower().replace("?", "").replace(",", "").split()
    keywords = [w for w in words if w not in stopwords and len(w) > 2]
    return keywords[:5]


def _extract_service_names_from_search(search_results: list[str]) -> list[str]:
    """Extract service names from search result text."""
    names = []
    for result in search_results:
        for line in result.split("\n"):
            if line.startswith("### "):
                name = line.replace("### ", "").strip()
                if name and name not in names:
                    names.append(name)
    return names


def _extract_service_name_from_question(question: str, index: str) -> list[str]:
    """Try to find exact service names mentioned in the question."""
    found = []
    # Get all service names from index
    for line in index.split("\n"):
        if "|" in line and "](services/" in line:
            match = re.search(r'\[([^\]]+)\]', line)
            if match:
                svc_name = match.group(1)
                if svc_name.lower() in question.lower():
                    found.append(svc_name)
    return found


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------


def score_answer(answer: str, expected_keywords: list[str]) -> dict[str, Any]:
    """Score an answer by checking for expected keywords."""
    if not answer:
        return {"score": 0, "matched": [], "missed": expected_keywords}

    answer_lower = answer.lower()
    matched = [kw for kw in expected_keywords if kw.lower() in answer_lower]
    missed = [kw for kw in expected_keywords if kw.lower() not in answer_lower]
    score = len(matched) / len(expected_keywords) if expected_keywords else 0

    return {"score": round(score, 2), "matched": matched, "missed": missed}


async def llm_judge_3way(question: str, brain_answer: str, brain_lite_answer: str, lite_answer: str) -> dict[str, Any]:
    """LLM judge comparing all 3 answers."""
    from dotenv import load_dotenv
    load_dotenv()

    import httpx
    from openai import AsyncAzureOpenAI
    from src.config.settings import get_settings

    settings = get_settings()
    client = AsyncAzureOpenAI(
        azure_endpoint=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_key,
        api_version=settings.azure_openai_api_version,
        http_client=httpx.AsyncClient(verify=False),
    )

    prompt = f"""You are evaluating 3 AI system answers about engineering microservices.

QUESTION: {question}

ANSWER A (Full Brain — vector search + graph DB + internal GPT):
{brain_answer[:1500]}

ANSWER B (Brain-Lite — vector search + graph DB + external LLM):
{brain_lite_answer[:1500]}

ANSWER C (Steering Lite — keyword file search + external LLM):
{lite_answer[:1500]}

Score each on 1-5 scale for: Accuracy, Completeness, Specificity, Usefulness.

Respond in this EXACT format:
SCORES_A: accuracy=X, completeness=X, specificity=X, usefulness=X
SCORES_B: accuracy=X, completeness=X, specificity=X, usefulness=X
SCORES_C: accuracy=X, completeness=X, specificity=X, usefulness=X
WINNER: A or B or C or TIE
REASONING: 2-3 sentences explaining the ranking."""

    try:
        response = await client.chat.completions.create(
            model=settings.azure_openai_deployment_gpt4o,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=500,
        )
        raw = response.choices[0].message.content or ""
        return _parse_3way_judge(raw)
    except Exception as exc:
        return {"brain": {}, "brain_lite": {}, "lite": {}, "winner": "ERROR", "reasoning": str(exc)}
    finally:
        await client.close()


def _parse_3way_judge(raw: str) -> dict[str, Any]:
    """Parse the 3-way judge response."""
    result: dict[str, Any] = {
        "brain": {"accuracy": 0, "completeness": 0, "specificity": 0, "usefulness": 0},
        "brain_lite": {"accuracy": 0, "completeness": 0, "specificity": 0, "usefulness": 0},
        "lite": {"accuracy": 0, "completeness": 0, "specificity": 0, "usefulness": 0},
        "winner": "TIE",
        "reasoning": "",
    }

    for line in raw.split("\n"):
        line = line.strip()
        nums = re.findall(r'=(\d)', line)
        if line.startswith("SCORES_A:") and len(nums) >= 4:
            result["brain"] = {"accuracy": int(nums[0]), "completeness": int(nums[1]), "specificity": int(nums[2]), "usefulness": int(nums[3])}
        elif line.startswith("SCORES_B:") and len(nums) >= 4:
            result["brain_lite"] = {"accuracy": int(nums[0]), "completeness": int(nums[1]), "specificity": int(nums[2]), "usefulness": int(nums[3])}
        elif line.startswith("SCORES_C:") and len(nums) >= 4:
            result["lite"] = {"accuracy": int(nums[0]), "completeness": int(nums[1]), "specificity": int(nums[2]), "usefulness": int(nums[3])}
        elif line.startswith("WINNER:"):
            w = line.replace("WINNER:", "").strip().upper()
            if "A" in w and "B" not in w and "C" not in w:
                result["winner"] = "Full Brain"
            elif "B" in w and "A" not in w and "C" not in w:
                result["winner"] = "Brain-Lite"
            elif "C" in w and "A" not in w and "B" not in w:
                result["winner"] = "Steering Lite"
            else:
                result["winner"] = "Tie"
        elif line.startswith("REASONING:"):
            result["reasoning"] = line.replace("REASONING:", "").strip()

    return result


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------


async def run_benchmark(difficulty: str | None = None) -> None:
    """Run the 3-way benchmark."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

    with open(QUESTIONS_FILE, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    questions = data["questions"]

    if difficulty:
        questions = [q for q in questions if q["difficulty"] == difficulty]

    logger.info("=" * 60)
    logger.info("SWE Bench — 3-Way MCP Evaluation")
    logger.info("  Questions: %d", len(questions))
    logger.info("  Contenders: Full Brain | Brain-Lite | Steering Lite")
    logger.info("=" * 60)

    results = []

    for idx, q in enumerate(questions, 1):
        qid = q["id"]
        question = q["question"]
        expected = q["expected_keywords"]
        logger.info("")
        logger.info("[%d/%d] %s", idx, len(questions), question[:70])

        entry: dict[str, Any] = {
            "id": qid,
            "question": question,
            "difficulty": q["difficulty"],
            "category": q["category"],
        }

        # 1. Full Brain
        brain_result = await call_full_brain(question)
        brain_answer = brain_result.get("answer") or ""
        brain_kw = score_answer(brain_answer, expected)
        entry["brain"] = {"answer": brain_answer[:500], "time": brain_result["time"], "error": brain_result["error"], **brain_kw}
        logger.info("  Brain:      kw=%.2f time=%.1fs", brain_kw["score"], brain_result["time"])

        # 2. Brain-Lite
        bl_result = await call_brain_lite(question)
        bl_answer = bl_result.get("answer") or ""
        bl_kw = score_answer(bl_answer, expected)
        entry["brain_lite"] = {"answer": bl_answer[:500], "time": bl_result["time"], "error": bl_result["error"], **bl_kw}
        logger.info("  Brain-Lite: kw=%.2f time=%.1fs", bl_kw["score"], bl_result["time"])

        # 3. Steering Lite
        lite_result = await call_steering_lite(question)
        lite_answer = lite_result.get("answer") or ""
        lite_kw = score_answer(lite_answer, expected)
        entry["lite"] = {"answer": lite_answer[:500], "time": lite_result["time"], "error": lite_result["error"], **lite_kw}
        logger.info("  Lite:       kw=%.2f time=%.1fs", lite_kw["score"], lite_result["time"])

        # 4. LLM Judge
        if brain_answer or bl_answer or lite_answer:
            logger.info("  Judging...")
            judge = await llm_judge_3way(question, brain_answer, bl_answer, lite_answer)
            entry["judge"] = judge
            logger.info("  Winner: %s", judge["winner"])

        results.append(entry)

        # Delay between questions to avoid Azure OpenAI rate limiting
        if idx < len(questions):
            await asyncio.sleep(3)

    _generate_report(results)


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------


def _generate_report(results: list[dict[str, Any]]) -> None:
    """Generate markdown + JSON reports."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y-%m-%dT%H-%M-%S")
    report_path = RESULTS_DIR / f"bench_{timestamp}.md"

    lines = [
        "# SWE Bench Results — 3-Way Comparison",
        "",
        f"**Date:** {datetime.now(UTC).isoformat()}",
        f"**Questions:** {len(results)}",
        "",
        "## Summary by Difficulty",
        "",
        "| Difficulty | Full Brain | Brain-Lite | Steering Lite | Brain Time | BL Time | Lite Time |",
        "|---|---|---|---|---|---|---|",
    ]

    for diff in ["easy", "medium", "hard", "expert"]:
        dr = [r for r in results if r["difficulty"] == diff]
        if not dr:
            continue
        b_avg = round(sum(r["brain"]["score"] for r in dr) / len(dr), 2)
        bl_avg = round(sum(r["brain_lite"]["score"] for r in dr) / len(dr), 2)
        l_avg = round(sum(r["lite"]["score"] for r in dr) / len(dr), 2)
        b_time = round(sum(r["brain"]["time"] for r in dr) / len(dr), 1)
        bl_time = round(sum(r["brain_lite"]["time"] for r in dr) / len(dr), 1)
        l_time = round(sum(r["lite"]["time"] for r in dr) / len(dr), 1)
        lines.append(f"| {diff} | {b_avg} | {bl_avg} | {l_avg} | {b_time}s | {bl_time}s | {l_time}s |")

    # Overall
    if results:
        b_total = round(sum(r["brain"]["score"] for r in results) / len(results), 2)
        bl_total = round(sum(r["brain_lite"]["score"] for r in results) / len(results), 2)
        l_total = round(sum(r["lite"]["score"] for r in results) / len(results), 2)
        lines.append(f"| **OVERALL** | **{b_total}** | **{bl_total}** | **{l_total}** | | | |")

    lines.append("")

    # Judge wins
    judge_wins = {"Full Brain": 0, "Brain-Lite": 0, "Steering Lite": 0, "Tie": 0}
    for r in results:
        w = r.get("judge", {}).get("winner", "Tie")
        judge_wins[w] = judge_wins.get(w, 0) + 1

    lines.append("## LLM Judge Wins")
    lines.append("")
    lines.append(f"| Full Brain | Brain-Lite | Steering Lite | Tie |")
    lines.append(f"|---|---|---|---|")
    lines.append(f"| {judge_wins.get('Full Brain', 0)} | {judge_wins.get('Brain-Lite', 0)} | {judge_wins.get('Steering Lite', 0)} | {judge_wins.get('Tie', 0)} |")
    lines.append("")

    # Per-question detail
    lines.append("## Per-Question Results")
    lines.append("")
    lines.append("| # | Question | Diff | Brain | BrainLite | Lite | Judge Winner |")
    lines.append("|---|----------|------|-------|-----------|------|-------------|")
    for r in results:
        jw = r.get("judge", {}).get("winner", "-")
        lines.append(f"| {r['id']} | {r['question'][:45]}... | {r['difficulty']} | {r['brain']['score']} | {r['brain_lite']['score']} | {r['lite']['score']} | {jw} |")

    lines.append("")

    # Detailed judge reasoning
    lines.append("## LLM Judge — Detailed Reasoning")
    lines.append("")
    for r in results:
        judge = r.get("judge", {})
        if not judge:
            continue
        lines.append(f"### {r['id']}: {r['question'][:80]}")
        lines.append("")
        lines.append(f"**Winner:** {judge.get('winner', '-')}")
        lines.append("")
        bs = judge.get("brain", {})
        bls = judge.get("brain_lite", {})
        ls = judge.get("lite", {})
        lines.append("| Criteria | Full Brain | Brain-Lite | Steering Lite |")
        lines.append("|----------|-----------|-----------|--------------|")
        for c in ["accuracy", "completeness", "specificity", "usefulness"]:
            lines.append(f"| {c.title()} | {bs.get(c, '-')}/5 | {bls.get(c, '-')}/5 | {ls.get(c, '-')}/5 |")
        lines.append("")
        lines.append(f"**Reasoning:** {judge.get('reasoning', '-')}")
        lines.append("")
        lines.append("<details><summary>Full Brain Answer</summary>")
        lines.append("")
        lines.append(f"```\n{r.get('brain', {}).get('answer', 'N/A')}\n```")
        lines.append("</details>")
        lines.append("")
        lines.append("<details><summary>Brain-Lite Answer</summary>")
        lines.append("")
        lines.append(f"```\n{r.get('brain_lite', {}).get('answer', 'N/A')}\n```")
        lines.append("</details>")
        lines.append("")
        lines.append("<details><summary>Steering Lite Answer</summary>")
        lines.append("")
        lines.append(f"```\n{r.get('lite', {}).get('answer', 'N/A')}\n```")
        lines.append("</details>")
        lines.append("")
        lines.append("---")
        lines.append("")

    report_path.write_text("\n".join(lines), encoding="utf-8")
    logger.info("")
    logger.info("Report: %s", report_path)

    # JSON
    json_path = RESULTS_DIR / f"bench_{timestamp}.json"
    json_path.write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="Run 3-way SWE Bench evaluation")
    parser.add_argument("--difficulty", type=str, help="Filter: easy/medium/hard/expert")
    args = parser.parse_args()
    asyncio.run(run_benchmark(difficulty=args.difficulty))


if __name__ == "__main__":
    main()
