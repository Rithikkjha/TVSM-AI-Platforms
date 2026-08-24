"""Catalog Classifier — chunked SLM classification of PRD into catalog work items.

Implements the 3-call strategy for gemma3:4b reliability:
- Call 1: System identification (targetSystems, scopeType, overheadFlags)
- Call 2: Work item classification (workItems[] — chunked for long PRDs)
- Call 3: Integration & risk analysis (integrationPatterns, assumptions, risks)

Each call is focused, under ~8K tokens of prompt, within the model's accuracy window.

Requirements: 1.1–1.6, 2.1–2.4 from catalog-based-estimation spec.
"""

import json
import logging
from typing import Any, Optional

from app.models.schemas import (
    CatalogClassificationResult,
    CatalogOverheadFlags,
    CatalogWorkItem,
    SLMOptions,
)
from app.services.catalog_loader import CatalogLoader
from app.services.slm_engine import SLMEngine

logger = logging.getLogger(__name__)

# Max chars per chunk for Call 2 — dynamically calculated based on PRD length
# Target: keep each chunk around 4000-5000 chars for gemma3:4b accuracy
# A 25-page PRD (~50K chars) would produce ~10-12 chunks
CHUNK_SIZE = 4500
# Always chunk — even short PRDs benefit from focused classification
CHUNK_THRESHOLD = 4500
# SLM options for classification calls
CLASSIFICATION_SLM_OPTIONS = SLMOptions(temperature=0.1, maxTokens=2048)

# Common system name aliases (SLM may use different names)
SYSTEM_NAME_ALIASES = {
    "website": "tvsmotor.com",
    "tvs website": "tvsmotor.com",
    "tvsmotor.com": "tvsmotor.com",
    "tvs motor website": "tvsmotor.com",
    "connect app": "TVS Connect",
    "tvs connect app": "TVS Connect",
    "mobile app": "TVS Connect",
    "app": "TVS Connect",
    "bs": "Booking Service",
    "booking service": "Booking Service",
    "booking svc": "Booking Service",
    "dms": "DMS",
    "ems": "EMS",
    "ems / accelerator": "EMS",
    "accelerator": "EMS",
    "subscription platform": "Booking Service",
    "subscription service": "Booking Service",
    "entitlement platform": "Booking Service",
    "catalogue service": "Catalog Service",
    "catalog service": "Catalog Service",
    "catalog": "Catalog Service",
    "catalogue": "Catalog Service",
    "pricing engine": "Catalog Service",
    "mdp": "MDP",
    "master data": "MDP",
    "cpg": "CPG",
    "juspay": "CPG",
    "cpg/juspay": "CPG",
    "payment gateway": "CPG",
    "cns": "CNS",
    "notification service": "CNS",
    "notifications": "CNS",
    "ums": "UMS",
    "identity": "UMS",
    "sso": "UMS",
    "idp": "IDP",
    "poms": "POMS",
    "poms/ioms": "POMS",
    "truchamp": "TruChamp",
    "motconnect": "TruChamp",
    "truchamp/motoconnect": "TruChamp",
    "cps": "CPS",
    "digiapp": "DigiApp",
    "digi app": "DigiApp",
    "sap": "DMS",
    "dealer locator": "Dealer Locator",
    "lead service": "Lead Service",
    "ls": "Lead Service",
    "dcp": "DCP",
    "aap": "AAP",
    "p360": "Booking Service",
    "vehicle systems": "TVS Connect",
    "vehicle": "TVS Connect",
    "cluster": "TVS Connect",
    "vcu": "TVS Connect",
    "tcu": "TVS Connect",
    "iqube": "TVS Connect",
    "iqube s": "TVS Connect",
    "iqube 09/ ug": "TVS Connect",
    "iqube 11": "TVS Connect",
    "iqube st": "TVS Connect",
    "apache": "TVS Connect",
    "ntorq": "TVS Connect",
    "raider": "TVS Connect",
    "jupiter": "TVS Connect",
    "ronin": "TVS Connect",
    "azure app service": "_CLOUD_HINT_",
    "azure devops": "_CLOUD_HINT_",
    "azure functions": "_CLOUD_HINT_",
    "azure service bus": "_CLOUD_HINT_",
    "azure cosmos db": "_CLOUD_HINT_",
    "azure blob": "_CLOUD_HINT_",
    "azure sql": "_CLOUD_HINT_",
    "azure redis": "_CLOUD_HINT_",
    "azure iot hub": "_CLOUD_HINT_",
    "azure cdn": "_CLOUD_HINT_",
    "azure api management": "_CLOUD_HINT_",
    "azure key vault": "_CLOUD_HINT_",
    "azure ad b2c": "_CLOUD_HINT_",
    "app insights": "_CLOUD_HINT_",
    "application insights": "_CLOUD_HINT_",
    "rs": "DMS",
    "reimbursement system": "DMS",
    "azure": "Booking Service",
    "azure services": "Booking Service",
    "middleware": "IDP",
    "all systems": "Booking Service",
}


class CatalogClassifier:
    """Orchestrates chunked SLM classification of PRD into catalog work items.

    Uses 3 sequential calls to keep each prompt focused and within
    gemma3:4b's reliable accuracy window.
    """

    def __init__(self, slm_engine: SLMEngine, loader: CatalogLoader):
        self.slm = slm_engine
        self.loader = loader

    async def classify(self, prd_text: str, project_name: str = "") -> CatalogClassificationResult:
        """Run the full 3-call classification pipeline.

        Args:
            prd_text: Full PRD/BRD text content.
            project_name: Project name for context.

        Returns:
            Merged ClassificationResult from all 3 calls.

        Raises:
            ClassificationError: If classification fails after retries.
        """
        # Create a summary for calls 1 and 3 (first + last sections for system identification)
        prd_start = prd_text[:4000]
        prd_end = prd_text[-3000:] if len(prd_text) > 4000 else ""
        prd_summary = prd_start + "\n\n...\n\n" + prd_end

        # Call 1: System identification
        systems_result = await self._call1_identify_systems(prd_summary, project_name)

        # Call 2: Work item classification
        work_items = await self._call2_classify_work_items(
            prd_text, systems_result.get("targetSystems", []), project_name
        )

        # Call 3: Integration & risk analysis
        integration_result = await self._call3_integration_risks(
            prd_summary, systems_result.get("targetSystems", [])
        )

        # Merge results
        overhead_raw = systems_result.get("overheadFlags", {})
        overhead_flags = CatalogOverheadFlags(
            teamSize=overhead_raw.get("teamSize", 3),
            crossDomain=overhead_raw.get("crossDomain", False),
            crossDomainSystems=overhead_raw.get("crossDomainSystems", []),
            techFamiliarityRisk=overhead_raw.get("techFamiliarityRisk", "proficient"),
            dataVolumeEstimate=overhead_raw.get("dataVolumeEstimate", "<1K"),
            multiRegion=overhead_raw.get("multiRegion", False),
            regionCount=overhead_raw.get("regionCount", 0),
            securityCritical=overhead_raw.get("securityCritical", False),
            legacyTechDebt=overhead_raw.get("legacyTechDebt", False),
        )

        return CatalogClassificationResult(
            requirementTitle=systems_result.get("requirementTitle", project_name or "Untitled"),
            targetSystems=[s for s in systems_result.get("targetSystems", []) if s != "_CLOUD_HINT_"],
            scopeType=systems_result.get("scopeType", "New Feature"),
            workItems=[w for w in work_items if w.system != "_CLOUD_HINT_"],
            integrationPatterns=integration_result.get("integrationPatterns", []),
            overheadFlags=overhead_flags,
            assumptions=integration_result.get("assumptions", []),
            risks=integration_result.get("risks", []),
        )

    async def _call1_identify_systems(self, prd_summary: str, project_name: str) -> dict[str, Any]:
        """Call 1: Identify target systems, scope type, and overhead flags.

        Prompt includes §3 (System Registry) from blueprint.
        """
        registry_section = self.loader.load_blueprint_section("§3")

        prompt = f"""You are a system analyst for TVS Motor Company.
Read this requirement and identify which systems are impacted.

{registry_section}

Project: {project_name}
PRD Content:
---
{prd_summary}
---

Analyze this PRD and return ONLY valid JSON:
{{"requirementTitle": "short title", "targetSystems": ["System1", "System2"], "scopeType": "New Feature | Enhancement | Bug Fix | Migration | Integration | New Application | New Module", "overheadFlags": {{"teamSize": 3, "crossDomain": false, "crossDomainSystems": [], "techFamiliarityRisk": "proficient", "dataVolumeEstimate": "<1K", "multiRegion": false, "regionCount": 0, "securityCritical": false, "legacyTechDebt": false}}}}

Rules:
- targetSystems must be names from the System Registry above
- scopeType: choose the most appropriate type:
  * "New Application" = building an entirely new platform/product from scratch (multiple new services, new DB, new frontend)
  * "New Module" = new functional module within an existing application
  * "New Feature" = new capability within existing module
  * "Enhancement" = extending/improving existing feature
  * "Bug Fix" = fixing broken behavior
  * "Integration" = connecting existing systems
  * "Migration" = moving data/systems
- teamSize: estimate based on scope complexity (3 for small, 5 for medium, 8+ for large)
- crossDomain: true if BOTH CP and D2C systems are involved
- securityCritical: true if payment or PII data is involved
- legacyTechDebt: true if touching legacy systems (ASMX, Web Forms, >5yr old)

Return ONLY valid JSON, no other text."""

        result = await self._call_slm_with_retry(prompt, "call1_systems")
        if result is None:
            # Fallback: minimal defaults
            return {
                "requirementTitle": project_name or "Untitled",
                "targetSystems": ["DMS"],
                "scopeType": "New Feature",
                "overheadFlags": {},
            }
        return result

    async def _call2_classify_work_items(
        self, prd_text: str, target_systems: list[str], project_name: str
    ) -> list[CatalogWorkItem]:
        """Call 2: Classify PRD into atomic work units.

        If PRD > 8K chars, splits into chunks and merges results.
        Prompt includes §1 (Principles), §2 (Catalog), §4 (Triggers).
        """
        principles = self.loader.load_blueprint_section("§1")
        catalog_section = self.loader.load_blueprint_section("§2")
        triggers = self.loader.load_blueprint_section("§4")

        # Determine if chunking needed
        if len(prd_text) > CHUNK_THRESHOLD:
            chunks = self._split_into_chunks(prd_text)
            logger.info(f"PRD too long ({len(prd_text)} chars), splitting into {len(chunks)} chunks")
        else:
            chunks = [prd_text]

        all_work_items: list[CatalogWorkItem] = []

        for i, chunk in enumerate(chunks):
            prompt = self._build_call2_prompt(
                chunk, target_systems, project_name, principles, catalog_section, triggers, i + 1, len(chunks)
            )
            result = await self._call_slm_with_retry(prompt, f"call2_items_chunk{i+1}")

            if result and "workItems" in result:
                items = self._parse_work_items(result["workItems"])
                all_work_items.extend(items)

        # Merge/deduplicate
        if len(chunks) > 1:
            all_work_items = self._merge_chunked_results(all_work_items)

        # Fallback if empty
        if not all_work_items:
            logger.warning("No work items classified — using default decomposition")
            all_work_items = self._default_decomposition(target_systems)

        return all_work_items

    async def _call3_integration_risks(
        self, prd_summary: str, target_systems: list[str]
    ) -> dict[str, Any]:
        """Call 3: Identify integration patterns, assumptions, and risks.

        Lightweight call using identified systems and pattern list.
        """
        prompt = f"""You are an integration analyst for TVS Motor Company.
Given these systems that a requirement touches, identify integration patterns, assumptions, and risks.

Systems identified: {', '.join(target_systems)}

Available integration patterns:
- REST_EXISTING: Calling an already-available REST endpoint
- REST_NEW: Building a new REST endpoint
- SERVICE_BUS_NEW_TOPIC: Creating a new Azure Service Bus topic
- SERVICE_BUS_NEW_SUBSCRIBER: Subscribing to an existing topic
- SAP_RFC: RFC/BAPI call to SAP
- SAP_IDOC: IDoc exchange with SAP
- BATCH_FILE: SFTP/blob file-based integration
- WEBHOOK: Webhook callback pattern
- GRPC: gRPC service communication
- GRAPHQL: GraphQL federation

PRD Summary:
---
{prd_summary}
---

Return ONLY valid JSON:
{{"integrationPatterns": ["PATTERN1", "PATTERN2"], "assumptions": ["assumption 1", "assumption 2"], "risks": ["risk 1", "risk 2"]}}

Rules:
- integrationPatterns: only use patterns from the list above
- assumptions: list things you assumed because the PRD didn't explicitly state them (max 5)
- risks: list gaps or concerns in the PRD that could affect estimation (max 5)

Return ONLY valid JSON, no other text."""

        result = await self._call_slm_with_retry(prompt, "call3_integration")
        if result is None:
            return {"integrationPatterns": [], "assumptions": [], "risks": []}
        return result

    def _build_call2_prompt(
        self,
        prd_chunk: str,
        target_systems: list[str],
        project_name: str,
        principles: str,
        catalog_section: str,
        triggers: str,
        chunk_num: int,
        total_chunks: int,
    ) -> str:
        """Build the work item classification prompt for a single chunk."""
        chunk_note = ""
        if total_chunks > 1:
            chunk_note = f"\n(This is chunk {chunk_num} of {total_chunks} of the PRD. Classify work items found in THIS section only.)\n"

        prompt = f"""You are a software effort classifier for TVS Motor Company.
{chunk_note}
{principles}

{catalog_section}

{triggers}

Target Systems (already identified): {', '.join(target_systems)}
Project: {project_name}

PRD Content:
---
{prd_chunk}
---

Classify this PRD section into work items from the catalog above.
Return ONLY valid JSON:
{{"workItems": [{{"unitId": "XX-NN", "complexity": "simple|medium|complex", "quantity": 1, "system": "SystemName", "reason": "one-line explanation"}}]}}

Rules:
- unitId MUST be from the catalog above (FE-01 through DO-12)
- complexity MUST be: simple, medium, or complex
- system MUST be from Target Systems listed above
- reason MUST explain WHY this unit was chosen
- Include testing (QA-*) and deployment (DO-*) items too
- Do NOT output effort numbers — only unit IDs and classifications

Return ONLY valid JSON, no other text."""
        return prompt

    async def _call_slm_with_retry(self, prompt: str, call_name: str) -> Optional[dict[str, Any]]:
        """Call SLM and parse JSON response. Retry once on failure.

        Args:
            prompt: The prompt to send.
            call_name: Label for logging.

        Returns:
            Parsed JSON dict, or None if both attempts fail.
        """
        for attempt in range(2):
            try:
                response = await self.slm.inference(prompt, options=CLASSIFICATION_SLM_OPTIONS)
                parsed = self._extract_json(response.content)
                if parsed is not None:
                    logger.info(f"[{call_name}] Success (attempt {attempt + 1})")
                    return parsed
                else:
                    logger.warning(
                        f"[{call_name}] Failed to parse JSON (attempt {attempt + 1}). "
                        f"Response: {response.content[:200]}..."
                    )
            except Exception as exc:
                logger.warning(f"[{call_name}] SLM call failed (attempt {attempt + 1}): {exc}")

        logger.error(f"[{call_name}] Failed after 2 attempts.")
        return None

    def _extract_json(self, content: str) -> Optional[dict[str, Any]]:
        """Extract JSON from SLM response (handles markdown code blocks, extra text)."""
        text = content.strip()

        # Strip markdown code blocks
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            parts = text.split("```")
            if len(parts) >= 3:
                text = parts[1].strip()
                if text.startswith("json"):
                    text = text[4:].strip()

        # Find JSON object
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            json_str = text[start:end]
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass

        # Try the whole text
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return None

    def _parse_work_items(self, raw_items: list[dict]) -> list[CatalogWorkItem]:
        """Parse and validate raw work item dicts from SLM response.

        Discards items with invalid unitId or complexity.
        Normalizes system names using aliases.
        """
        valid_unit_ids = self.loader.get_unit_ids()
        valid_complexities = {"simple", "medium", "complex"}
        valid_systems = self.loader.get_system_names()

        items = []
        for raw in raw_items:
            unit_id = raw.get("unitId", "")
            complexity = raw.get("complexity", "medium")
            quantity = raw.get("quantity", 1)
            system = raw.get("system", "")
            reason = raw.get("reason", "Classified by SLM")

            # Validate unitId
            if unit_id not in valid_unit_ids:
                logger.warning(f"Invalid unitId '{unit_id}' — discarding")
                continue

            # Normalize complexity
            if complexity not in valid_complexities:
                logger.warning(f"Invalid complexity '{complexity}' for {unit_id} — defaulting to medium")
                complexity = "medium"

            # Validate quantity
            if not isinstance(quantity, int) or quantity < 1:
                quantity = 1

            # Normalize system name using aliases
            system = self._normalize_system_name(system, valid_systems)

            items.append(CatalogWorkItem(
                unitId=unit_id,
                complexity=complexity,
                quantity=quantity,
                system=system,
                reason=reason,
            ))

        return items

    def _normalize_system_name(self, system: str, valid_systems: set[str]) -> str:
        """Normalize a system name using aliases and fuzzy matching.

        Args:
            system: Raw system name from SLM.
            valid_systems: Set of valid system names from registry.

        Returns:
            Normalized system name (from registry or best guess).
            Returns "_CLOUD_HINT_" for Azure infrastructure terms (filtered later).
        """
        # Direct match
        if system in valid_systems:
            return system

        # Try alias lookup (case-insensitive)
        alias_key = system.lower().strip()
        if alias_key in SYSTEM_NAME_ALIASES:
            return SYSTEM_NAME_ALIASES[alias_key]

        # Try partial match (system name contains a known system)
        for valid in valid_systems:
            if valid.lower() in alias_key or alias_key in valid.lower():
                return valid

        # Check if it's a cloud/infrastructure term — return cloud hint marker
        cloud_keywords = ["azure", "aws", "gcp", "cloud", "kubernetes", "k8s", "docker", "terraform"]
        if any(kw in alias_key for kw in cloud_keywords):
            logger.info(f"Cloud resource '{system}' detected — marking as cloud hint")
            return "_CLOUD_HINT_"

        # No match found — use default with warning
        logger.warning(f"Unknown system '{system}' — defaulting to 'DMS'")
        return "DMS"

    def _merge_chunked_results(self, items: list[CatalogWorkItem]) -> list[CatalogWorkItem]:
        """Merge work items from multiple chunks.

        Deduplication: if same unitId + system + complexity appears multiple times,
        sum the quantities. Different complexities for same unitId+system are kept separate.
        """
        merged: dict[str, CatalogWorkItem] = {}

        for item in items:
            key = f"{item.unitId}:{item.system}:{item.complexity}"
            if key in merged:
                # Sum quantities
                existing = merged[key]
                merged[key] = existing.model_copy(
                    update={"quantity": existing.quantity + item.quantity}
                )
            else:
                merged[key] = item

        return list(merged.values())

    def _split_into_chunks(self, text: str) -> list[str]:
        """Split text into chunks at section/heading boundaries.

        Strategy:
        - Split at markdown headings (##, ###) or double newlines
        - Target ~4500 chars per chunk
        - Cap at 8 chunks max (to keep total SLM calls reasonable)
        - For very large docs (>40K), increase chunk size to stay within 8 calls
        """
        # Dynamic chunk size: for large docs, increase chunk size to cap at 8 calls
        max_chunks = 8
        target_chunk_size = max(CHUNK_SIZE, len(text) // max_chunks)

        # Try to split at heading boundaries first
        import re
        sections = re.split(r'\n(?=#{1,3}\s)', text)

        chunks = []
        current_chunk = ""

        for section in sections:
            # If adding this section exceeds target, start new chunk
            if len(current_chunk) + len(section) > target_chunk_size and current_chunk.strip():
                chunks.append(current_chunk.strip())
                current_chunk = section
            else:
                current_chunk += "\n" + section

        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        # If heading-based splitting produced too few chunks (e.g., no headings in doc),
        # fall back to paragraph-based splitting
        if len(chunks) <= 1 and len(text) > target_chunk_size:
            chunks = []
            paragraphs = text.split("\n\n")
            current_chunk = ""
            for para in paragraphs:
                if len(current_chunk) + len(para) > target_chunk_size and current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = para
                else:
                    current_chunk += "\n\n" + para
            if current_chunk.strip():
                chunks.append(current_chunk.strip())

        # Ensure at least one chunk
        if not chunks:
            chunks = [text[:target_chunk_size]]

        # Cap at max_chunks — merge smallest adjacent chunks if over limit
        while len(chunks) > max_chunks:
            # Find smallest adjacent pair and merge
            min_combined = float('inf')
            min_idx = 0
            for i in range(len(chunks) - 1):
                combined = len(chunks[i]) + len(chunks[i + 1])
                if combined < min_combined:
                    min_combined = combined
                    min_idx = i
            chunks[min_idx] = chunks[min_idx] + "\n\n" + chunks[min_idx + 1]
            chunks.pop(min_idx + 1)

        logger.info(
            f"PRD split into {len(chunks)} chunks "
            f"(total {len(text)} chars, target {target_chunk_size} chars/chunk, "
            f"actual range: {min(len(c) for c in chunks)}-{max(len(c) for c in chunks)} chars)"
        )
        return chunks

    def _default_decomposition(self, target_systems: list[str]) -> list[CatalogWorkItem]:
        """Fallback decomposition when SLM fails to classify.

        Uses the 'New module' default from §4 trigger dictionary.
        """
        system = target_systems[0] if target_systems else "DMS"
        return [
            CatalogWorkItem(unitId="FE-01", complexity="medium", quantity=2, system=system, reason="Default: info pages"),
            CatalogWorkItem(unitId="FE-02", complexity="medium", quantity=1, system=system, reason="Default: input form"),
            CatalogWorkItem(unitId="FE-04", complexity="medium", quantity=1, system=system, reason="Default: data table"),
            CatalogWorkItem(unitId="BE-01", complexity="medium", quantity=2, system=system, reason="Default: CRUD APIs"),
            CatalogWorkItem(unitId="BE-02", complexity="medium", quantity=1, system=system, reason="Default: business logic"),
            CatalogWorkItem(unitId="QA-01", complexity="medium", quantity=1, system=system, reason="Default: unit tests"),
        ]
