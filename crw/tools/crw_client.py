"""
Shared HTTP client for CRW API.
Handles authentication, retries, and base URL resolution.
"""

import json
import logging
import time
from collections.abc import Mapping
from typing import Any

import requests
from requests.exceptions import HTTPError

logger = logging.getLogger(__name__)

DEFAULT_BASE_URL = "https://fastcrw.com/api"


class CrwClient:
    def __init__(self, api_key: str, base_url: str | None = None):
        self.api_key = api_key
        self.base_url = (base_url or DEFAULT_BASE_URL).rstrip("/")

    def _headers(self) -> dict[str, str]:
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

    def _request(
        self,
        method: str,
        path: str,
        data: Mapping[str, Any] | None = None,
        retries: int = 3,
        backoff_factor: float = 0.3,
    ) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        for i in range(retries):
            try:
                resp = requests.request(
                    method, url, json=data, headers=self._headers(), timeout=120
                )
                resp.raise_for_status()
                result = resp.json()
                if not result.get("success", True):
                    error_msg = result.get("error", "Unknown error")
                    raise HTTPError(f"CRW API error: {error_msg}")
                return result
            except requests.exceptions.RequestException:
                if i < retries - 1:
                    time.sleep(backoff_factor * (2**i))
                else:
                    raise
        raise HTTPError("Request failed after retries")

    def scrape(self, url: str, **kwargs: Any) -> dict[str, Any]:
        return self._request("POST", "/v1/scrape", {"url": url, **kwargs})

    def crawl(self, url: str, **kwargs: Any) -> dict[str, Any]:
        return self._request("POST", "/v1/crawl", {"url": url, **kwargs})

    def crawl_status(self, job_id: str) -> dict[str, Any]:
        return self._request("GET", f"/v1/crawl/{job_id}")

    def cancel_crawl(self, job_id: str) -> dict[str, Any]:
        return self._request("DELETE", f"/v1/crawl/{job_id}")

    def search(self, query: str, **kwargs: Any) -> dict[str, Any]:
        """Search the web. Cloud-only feature."""
        return self._request("POST", "/v1/search", {"query": query, **kwargs})

    def map(self, url: str, **kwargs: Any) -> dict[str, Any]:
        return self._request("POST", "/v1/map", {"url": url, **kwargs})

    def poll_crawl(self, job_id: str, interval: int = 5) -> dict[str, Any]:
        while True:
            status = self.crawl_status(job_id)
            if status.get("status") == "completed":
                return status
            if status.get("status") == "failed":
                raise HTTPError(f"Crawl failed: {status.get('error', 'unknown')}")
            time.sleep(interval)


def get_array_params(params: dict[str, Any], key: str) -> list[str] | None:
    value = params.get(key)
    if value and isinstance(value, str):
        return [s.strip() for s in value.split(",") if s.strip()]
    return None


def get_json_params(params: dict[str, Any], key: str) -> Any | None:
    value = params.get(key)
    if value and isinstance(value, str):
        try:
            return json.loads(value.replace("'", '"'))
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON in parameter '{key}'")
    return None
