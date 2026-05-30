"""Sub-client for the Companies endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Dict, Optional, Union
from uuid import UUID

import httpx

from jobo_enterprise.exceptions import _handle_error
from jobo_enterprise.models import Company, JobSearchResponse


def _jobs_params(
    posted_after: Optional[datetime], page: int, page_size: int
) -> Dict[str, Union[str, int]]:
    params: Dict[str, Union[str, int]] = {"page": page, "page_size": page_size}
    if posted_after:
        params["posted_after"] = posted_after.isoformat()
    return params


class CompaniesClient:
    """Synchronous sub-client for the Companies endpoints.

    Access via ``client.companies``.
    """

    def __init__(self, http: httpx.Client) -> None:
        self._client = http

    def get(self, company_id: Union[UUID, str]) -> Company:
        """Fetch a fully enriched company profile (GET /api/companies/{id}).

        This endpoint is public — no API key required.

        Args:
            company_id: The Jobo company UUID.

        Returns:
            A :class:`Company` with the full enriched profile.
        """
        resp = self._client.get(f"/api/companies/{company_id}")
        if resp.status_code != 200:
            _handle_error(resp)
        return Company.model_validate(resp.json())

    def get_jobs(
        self,
        company_id: Union[UUID, str],
        *,
        posted_after: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 25,
    ) -> JobSearchResponse:
        """List jobs that belong to a specific company (GET /api/companies/{id}/jobs).

        Args:
            company_id: The Jobo company UUID.
            posted_after: Only jobs posted after this UTC datetime.
            page: Page number (1-indexed).
            page_size: Results per page (1–100).

        Returns:
            A :class:`JobSearchResponse` scoped to this company.
        """
        params = _jobs_params(posted_after, page, page_size)
        resp = self._client.get(f"/api/companies/{company_id}/jobs", params=params)
        if resp.status_code != 200:
            _handle_error(resp)
        return JobSearchResponse.model_validate(resp.json())


class AsyncCompaniesClient:
    """Asynchronous sub-client for the Companies endpoints.

    Access via ``client.companies``.
    """

    def __init__(self, http: httpx.AsyncClient) -> None:
        self._client = http

    async def get(self, company_id: Union[UUID, str]) -> Company:
        """Fetch a fully enriched company profile (GET /api/companies/{id})."""
        resp = await self._client.get(f"/api/companies/{company_id}")
        if resp.status_code != 200:
            _handle_error(resp)
        return Company.model_validate(resp.json())

    async def get_jobs(
        self,
        company_id: Union[UUID, str],
        *,
        posted_after: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 25,
    ) -> JobSearchResponse:
        """List jobs that belong to a specific company (GET /api/companies/{id}/jobs)."""
        params = _jobs_params(posted_after, page, page_size)
        resp = await self._client.get(f"/api/companies/{company_id}/jobs", params=params)
        if resp.status_code != 200:
            _handle_error(resp)
        return JobSearchResponse.model_validate(resp.json())
