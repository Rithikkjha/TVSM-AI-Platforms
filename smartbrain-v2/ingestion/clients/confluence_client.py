"""Concrete Confluence HTTP client implementing the ConfluenceMCPClient protocol.

Calls the Confluence REST API using httpx with Basic auth
(email:token). Supports both regular spaces and restricted spaces
(fetching child pages under a specific parent page).

Designed to satisfy the
:class:`~src.ingestion.orchestrator.ConfluenceMCPClient` protocol.
"""

from __future__ import annotations

import base64
import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class ConfluenceHTTPClient:
    """Concrete Confluence client using httpx to call Confluence REST API."""

    name: str = "confluence"
    source_type: str = "confluence"

    def __init__(
        self,
        url: str,
        email: str,
        token: str,
        spaces: list[str],
        restricted_spaces: list[dict[str, Any]] | None = None,
    ) -> None:
        self._url = url.rstrip("/")
        self.site_url = self._url  # public attr used by orchestrator to build absolute URLs
        self._email = email
        self._token = token
        self._spaces = spaces
        self._restricted_spaces: list[dict[str, Any]] = restricted_spaces or []

        # Basic auth: base64(email:token)
        credentials = base64.b64encode(f"{email}:{token}".encode()).decode()
        self._client = httpx.AsyncClient(
            verify=False,
            base_url=f"{self._url}/rest/api",
            headers={
                "Authorization": f"Basic {credentials}",
                "Accept": "application/json",
            },
            timeout=60.0,
        )

    def _get_parent_page_id(self, space_key: str) -> str | None:
        """Check if a space_key is restricted and return its parent_page_id."""
        for entry in self._restricted_spaces:
            if entry.get("space_key") == space_key:
                return entry.get("parent_page_id")
        return None

    async def get_pages(self, space_key: str) -> list[dict[str, Any]]:
        """Fetch ALL pages from a space using pagination.

        For regular spaces: GET /content?spaceKey={key}&type=page&limit=50&expand=...
        For restricted spaces (with parent_page_id):
            GET /content/{parent_page_id}/child/page?limit=50&expand=...
        
        Paginates through all results until no more pages are available.
        """
        parent_page_id = self._get_parent_page_id(space_key)
        expand = "body.storage,version,space"
        all_pages: list[dict[str, Any]] = []
        start = 0
        page_size = 50

        logger.info("Fetching pages for space %s", space_key)

        try:
            while True:
                if parent_page_id:
                    logger.info(
                        "Space %s is restricted — fetching descendants of page %s (start=%d)",
                        space_key,
                        parent_page_id,
                        start,
                    )
                    resp = await self._client.get(
                        f"/content/{parent_page_id}/descendant/page",
                        params={
                            "limit": str(page_size),
                            "start": str(start),
                            "expand": expand,
                        },
                    )
                else:
                    resp = await self._client.get(
                        "/content",
                        params={
                            "spaceKey": space_key,
                            "type": "page",
                            "limit": str(page_size),
                            "start": str(start),
                            "expand": expand,
                        },
                    )

                if resp.status_code == 429:
                    logger.warning("Rate limited fetching pages for space %s", space_key)
                    break
                resp.raise_for_status()
                data = resp.json()
                pages: list[dict[str, Any]] = data.get("results", [])
                all_pages.extend(pages)

                # Check if there are more pages
                size = data.get("size", 0)
                if size < page_size:
                    break  # No more pages
                start += page_size
                logger.info("  Fetched %d pages so far for space %s...", len(all_pages), space_key)

            logger.info("Fetched %d total pages for space %s", len(all_pages), space_key)
            return all_pages
        except httpx.HTTPStatusError as exc:
            logger.error(
                "Failed to fetch pages for space %s: %s %s",
                space_key,
                exc.response.status_code,
                exc.response.reason_phrase,
            )
            return all_pages
        except httpx.HTTPError as exc:
            logger.error("HTTP error fetching pages for space %s: %s", space_key, exc)
            return all_pages

    async def close(self) -> None:
        """Close the underlying httpx client."""
        await self._client.aclose()
