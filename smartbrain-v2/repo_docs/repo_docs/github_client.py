"""Minimal GitHub REST client (stdlib urllib). Only what phase 0 needs: list org repos."""

from __future__ import annotations

import json
import logging
import random
import re
import time
import urllib.error
import urllib.request
from typing import Any

from .secrets import redact, secret_forms

log = logging.getLogger(__name__)


class GitHubError(RuntimeError):
    pass


def normalize_repo(r: dict[str, Any]) -> dict[str, Any]:
    size = int(r.get("size") or 0)
    return {
        "name": r["name"],
        "full_name": r.get("full_name"),
        "default_branch": r.get("default_branch") or "main",
        "language": r.get("language"),
        "size_kb": size,
        "archived": bool(r.get("archived")),
        "empty": size == 0,
        "pushed_at": r.get("pushed_at"),
        "html_url": r.get("html_url"),
    }


class GitHubClient:
    def __init__(self, token: str, api_base: str = "https://api.github.com", max_retries: int = 4,
                 sleep=time.sleep):
        self._token = token
        self.api_base = api_base.rstrip("/")
        self.max_retries = max_retries
        self._sleep = sleep
        self._secrets = secret_forms(token)

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "smartbrain-repo-docs",
        }

    def _get(self, url: str) -> tuple[Any, dict[str, str]]:
        attempt = 0
        while True:
            req = urllib.request.Request(url, headers=self._headers())
            try:
                with urllib.request.urlopen(req, timeout=60) as resp:
                    body = resp.read().decode("utf-8")
                    return json.loads(body), {k.lower(): v for k, v in resp.headers.items()}
            except urllib.error.HTTPError as e:
                hdrs = {k.lower(): v for k, v in (e.headers or {}).items()}
                rate_limited = e.code == 429 or (
                    e.code == 403 and hdrs.get("x-ratelimit-remaining") == "0"
                )
                if not rate_limited and e.code < 500:
                    raise GitHubError(redact(f"GET {url} -> HTTP {e.code} {e.reason}",
                                             self._secrets)) from None
                wait = self._wait_for(hdrs, attempt)
                err = f"HTTP {e.code}"
            except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
                wait = self._wait_for({}, attempt)
                err = redact(str(e), self._secrets)
            attempt += 1
            if attempt > self.max_retries:
                raise GitHubError(f"GET {url} failed after {attempt} attempts: {err}")
            log.warning("GET %s: %s; retry %d in %.0fs", url, err, attempt, wait)
            self._sleep(wait)

    @staticmethod
    def _wait_for(hdrs: dict[str, str], attempt: int) -> float:
        if hdrs.get("retry-after", "").isdigit():
            return float(hdrs["retry-after"])
        reset = hdrs.get("x-ratelimit-reset")
        if hdrs.get("x-ratelimit-remaining") == "0" and reset and reset.isdigit():
            return max(1.0, min(900.0, float(reset) - time.time() + 1))
        return 2 ** (attempt + 1) + random.uniform(0, 1)

    def list_org_repos(self, org: str) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        page = 1
        url: str | None = f"{self.api_base}/orgs/{org}/repos?type=all&per_page=100&page=1"
        while url:
            data, hdrs = self._get(url)
            if not isinstance(data, list):
                raise GitHubError(f"unexpected response for {org} page {page}")
            out.extend(normalize_repo(r) for r in data)
            m = re.search(r'<([^>]+)>;\s*rel="next"', hdrs.get("link", ""))
            if m:
                url = m.group(1)
            elif len(data) == 100:
                page += 1
                url = f"{self.api_base}/orgs/{org}/repos?type=all&per_page=100&page={page}"
            else:
                url = None
        return out
