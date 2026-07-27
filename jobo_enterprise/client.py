"""Synchronous and asynchronous clients for the Jobo Enterprise API."""

from __future__ import annotations

from typing import Optional

import httpx

from jobo_enterprise.feed import JobsFeedClient, AsyncJobsFeedClient
from jobo_enterprise.search import JobsSearchClient, AsyncJobsSearchClient
from jobo_enterprise.companies import CompaniesClient, AsyncCompaniesClient
from jobo_enterprise.locations import LocationsClient, AsyncLocationsClient
from jobo_enterprise._transport import DEFAULT_FEED_TIMEOUT

_DEFAULT_BASE_URL = "https://connect.jobo.world"
_DEFAULT_TIMEOUT = 30.0
_USER_AGENT = "jobo-python/4.0.0"


class JoboClient:
    """Synchronous client for the Jobo Enterprise API.

    Access feature-specific sub-clients via properties:

    - ``client.feed`` — Bulk job feed with cursor-based pagination
    - ``client.search`` — Full-text job search with filters
    - ``client.companies`` — Enriched company profiles and per-company jobs
    - ``client.locations`` — Geocoding and location resolution

    Args:
        api_key: Your Jobo Enterprise API key.
        base_url: API base URL. Defaults to ``https://connect.jobo.world``.
        timeout: Request timeout in seconds. Defaults to 30.
        feed_timeout: Response timeout in seconds for the two feed endpoints,
            which stream up to 1,000 full job records per call. Defaults to 120.
        httpx_client: Optional pre-configured ``httpx.Client`` instance.
    """

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = _DEFAULT_BASE_URL,
        timeout: float = _DEFAULT_TIMEOUT,
        feed_timeout: float = DEFAULT_FEED_TIMEOUT,
        httpx_client: Optional[httpx.Client] = None,
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._client = httpx_client or httpx.Client(
            base_url=self._base_url,
            timeout=timeout,
            headers={
                "X-Api-Key": api_key,
                "User-Agent": _USER_AGENT,
                "Accept": "application/json",
            },
        )

        self.feed = JobsFeedClient(self._client, feed_timeout=feed_timeout)
        """Bulk job feed with cursor-based pagination."""

        self.search = JobsSearchClient(self._client)
        """Full-text job search with filters and pagination."""

        self.companies = CompaniesClient(self._client)
        """Enriched company profiles and per-company job listings."""

        self.locations = LocationsClient(self._client)
        """Geocoding and location resolution."""

    def close(self) -> None:
        """Close the underlying HTTP client."""
        self._client.close()

    def __enter__(self) -> "JoboClient":
        return self

    def __exit__(self, *args: object) -> None:
        self.close()


class AsyncJoboClient:
    """Asynchronous client for the Jobo Enterprise API.

    Access feature-specific sub-clients via properties:

    - ``client.feed`` — Bulk job feed with cursor-based pagination
    - ``client.search`` — Full-text job search with filters
    - ``client.companies`` — Enriched company profiles and per-company jobs
    - ``client.locations`` — Geocoding and location resolution

    Args:
        api_key: Your Jobo Enterprise API key.
        base_url: API base URL. Defaults to ``https://connect.jobo.world``.
        timeout: Request timeout in seconds. Defaults to 30.
        feed_timeout: Response timeout in seconds for the two feed endpoints,
            which stream up to 1,000 full job records per call. Defaults to 120.
        httpx_client: Optional pre-configured ``httpx.AsyncClient`` instance.
    """

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = _DEFAULT_BASE_URL,
        timeout: float = _DEFAULT_TIMEOUT,
        feed_timeout: float = DEFAULT_FEED_TIMEOUT,
        httpx_client: Optional[httpx.AsyncClient] = None,
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._client = httpx_client or httpx.AsyncClient(
            base_url=self._base_url,
            timeout=timeout,
            headers={
                "X-Api-Key": api_key,
                "User-Agent": _USER_AGENT,
                "Accept": "application/json",
            },
        )

        self.feed = AsyncJobsFeedClient(self._client, feed_timeout=feed_timeout)
        """Bulk job feed with cursor-based pagination."""

        self.search = AsyncJobsSearchClient(self._client)
        """Full-text job search with filters and pagination."""

        self.companies = AsyncCompaniesClient(self._client)
        """Enriched company profiles and per-company job listings."""

        self.locations = AsyncLocationsClient(self._client)
        """Geocoding and location resolution."""

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self._client.aclose()

    async def __aenter__(self) -> "AsyncJoboClient":
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.close()
