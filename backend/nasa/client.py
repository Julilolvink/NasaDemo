from __future__ import annotations

import time
from typing import Any, Dict, Optional

import requests

from config import settings


class EONETClientError(RuntimeError):
    """Raised when the EONET API call fails in a non-recoverable way."""


class EONETClient:
    """
    Minimal EONET v3 client.

    Uses retries + backoff to handle transient network issues.
    EONET endpoint examples:
      /events?category=wildfires&status=open
      /categories
      /sources
    Docs: https://eonet.gsfc.nasa.gov/docs/v3
    """

    def __init__(
        self,
        base_url: str | None = None,
        timeout_seconds: int | None = None,
        retries: int | None = None,
        backoff_seconds: float | None = None,
        session: Optional[requests.Session] = None,
    ) -> None:
        self.base_url = (base_url or settings.EONET_BASE_URL).rstrip("/")
        self.timeout = timeout_seconds or settings.HTTP_TIMEOUT_SECONDS
        self.retries = retries if retries is not None else settings.HTTP_RETRIES
        self.backoff = backoff_seconds if backoff_seconds is not None else settings.HTTP_BACKOFF_SECONDS
        self.session = session or requests.Session()

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = f"{self.base_url}/{path.lstrip('/')}"
        last_err: Exception | None = None

        for attempt in range(1, self.retries + 1):
            try:
                resp = self.session.get(url, params=params or {}, timeout=self.timeout)
                # Treat 5xx as retryable; 4xx usually not.
                if 500 <= resp.status_code < 600:
                    raise requests.HTTPError(f"Server error {resp.status_code}", response=resp)

                resp.raise_for_status()
                return resp.json()
            except (requests.Timeout, requests.ConnectionError, requests.HTTPError) as e:
                last_err = e
                # If it's a 4xx, don't retry (except sometimes 429, but EONET typically is lenient).
                if isinstance(e, requests.HTTPError) and e.response is not None:
                    status = e.response.status_code
                    if 400 <= status < 500 and status != 429:
                        raise EONETClientError(f"EONET request failed ({status}) at {url}") from e

                if attempt < self.retries:
                    time.sleep(self.backoff * attempt)
                else:
                    raise EONETClientError(f"EONET request failed after retries at {url}") from last_err

        # Should never reach here
        raise EONETClientError(f"EONET request failed unexpectedly at {url}") from last_err

    # Public methods
    def get_events(
        self,
        category: str | None = None,
        source: str | None = None,
        status: str | None = None,   # "open" or "closed" (as per docs)
        days: int | None = None,     # last N days filter
        limit: int | None = None,
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {}
        if category:
            params["category"] = category
        if source:
            params["source"] = source
        if status:
            params["status"] = status
        if days is not None:
            params["days"] = days
        if limit is not None:
            params["limit"] = limit

        return self._get("/events", params=params)

    def get_categories(self) -> Dict[str, Any]:
        return self._get("/categories")

    def get_sources(self) -> Dict[str, Any]:
        return self._get("/sources")
