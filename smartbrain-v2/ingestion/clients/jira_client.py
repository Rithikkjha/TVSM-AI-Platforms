"""Concrete Jira HTTP client implementing the JiraMCPClient protocol.

Calls the Atlassian REST API v3 using httpx with Basic auth
(email:token). Designed to satisfy the
:class:`~src.ingestion.orchestrator.JiraMCPClient` protocol.
"""

from __future__ import annotations

import base64
import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class JiraHTTPClient:
    """Concrete Jira client using httpx to call Atlassian REST API v3."""

    name: str = "jira"
    source_type: str = "jira"

    def __init__(self, url: str, email: str, token: str, projects: list[str]) -> None:
        self._url = url.rstrip("/")
        self._email = email
        self._token = token
        self._projects = projects

        # Basic auth: base64(email:token)
        credentials = base64.b64encode(f"{email}:{token}".encode()).decode()
        self._client = httpx.AsyncClient(
            verify=False,
            base_url=f"{self._url}/rest/api/3",
            headers={
                "Authorization": f"Basic {credentials}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            timeout=30.0,
        )

    async def get_issues(self, project_key: str, max_issues: int = 500) -> list[dict[str, Any]]:
        """Fetch issues for a project using JQL, ordered by updated DESC.

        Uses the new ``GET /rest/api/3/search/jql`` endpoint that replaced
        the deprecated ``/rest/api/3/search`` in Atlassian Cloud (the old
        endpoint now returns HTTP 410 Gone). The new endpoint paginates
        with an opaque ``nextPageToken`` rather than ``startAt`` offsets,
        so we loop until ``isLast`` is true (or the token stops being
        returned) to fetch every matching issue.

        Args:
            project_key: Jira project key (e.g. "CCP10")
            max_issues: Maximum number of issues to fetch (default 500).
        """

        jql = f"project={project_key} ORDER BY updated DESC"
        fields = "summary,status,priority,description,assignee,issuetype,created,updated"
        page_size = 100
        all_issues: list[dict[str, Any]] = []
        next_token: str | None = None

        logger.info("Fetching issues for project %s (max %d)", project_key, max_issues)
        try:
            while True:
                params: dict[str, str] = {
                    "jql": jql,
                    "maxResults": str(min(page_size, max_issues - len(all_issues))),
                    "fields": fields,
                }
                if next_token:
                    params["nextPageToken"] = next_token

                resp = await self._client.get("/search/jql", params=params)
                if resp.status_code == 429:
                    logger.warning(
                        "Rate limited fetching issues for project %s at token=%r",
                        project_key,
                        next_token,
                    )
                    break
                resp.raise_for_status()
                data = resp.json()
                page_issues: list[dict[str, Any]] = data.get("issues", [])
                all_issues.extend(page_issues)

                # Cap at max_issues
                if len(all_issues) >= max_issues:
                    all_issues = all_issues[:max_issues]
                    break

                is_last = bool(data.get("isLast"))
                next_token = data.get("nextPageToken")

                if is_last or not next_token or not page_issues:
                    break
                logger.info(
                    "  Fetched %d issues so far for project %s...",
                    len(all_issues),
                    project_key,
                )

            logger.info(
                "Fetched %d total issues for project %s", len(all_issues), project_key
            )
            return all_issues
        except httpx.HTTPStatusError as exc:
            logger.error(
                "Failed to fetch issues for project %s: %s %s",
                project_key,
                exc.response.status_code,
                exc.response.reason_phrase,
            )
            return all_issues
        except httpx.HTTPError as exc:
            logger.error("HTTP error fetching issues for project %s: %s", project_key, exc)
            return all_issues

    async def close(self) -> None:
        """Close the underlying httpx client."""
        await self._client.aclose()
