"""Sub-client for the Jobs Search endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Any, AsyncIterator, Dict, Iterator, List, Optional

import httpx

from jobo_enterprise.exceptions import _handle_error
from jobo_enterprise.models import (
    InclusionExclusionFilter,
    Job,
    JobSearchBodyRequest,
    JobSearchResponse,
    RangeFilter,
)


def _simple_params(
    *,
    q: Optional[str],
    location: Optional[str],
    sources: Optional[str],
    work_model: Optional[str],
    employment_type: Optional[str],
    experience_level: Optional[str],
    posted_after: Optional[datetime],
    min_salary_usd: Optional[int],
    max_salary_usd: Optional[int],
    skills: Optional[str],
    industries: Optional[str],
    include_facets: Optional[str],
    page: int,
    page_size: int,
) -> Dict[str, Any]:
    params: Dict[str, Any] = {}
    if q:
        params["q"] = q
    if location:
        params["location"] = location
    if sources:
        params["sources"] = sources
    if work_model:
        params["work_model"] = work_model
    if employment_type:
        params["employment_type"] = employment_type
    if experience_level:
        params["experience_level"] = experience_level
    if posted_after:
        params["posted_after"] = posted_after.isoformat()
    if min_salary_usd is not None:
        params["min_salary_usd"] = min_salary_usd
    if max_salary_usd is not None:
        params["max_salary_usd"] = max_salary_usd
    if skills:
        params["skills"] = skills
    if industries:
        params["industries"] = industries
    if include_facets is not None:
        params["include_facets"] = include_facets
    params["page"] = page
    params["page_size"] = page_size
    return params


def _build_body(
    *,
    queries: Optional[List[str]],
    locations: Optional[List[str]],
    sources: Optional[List[str]],
    skills: Optional[InclusionExclusionFilter],
    companies: Optional[InclusionExclusionFilter],
    industries: Optional[InclusionExclusionFilter],
    work_models: Optional[List[str]],
    employment_types: Optional[List[str]],
    experience_levels: Optional[List[str]],
    salary_usd: Optional[RangeFilter],
    posted_after: Optional[datetime],
    include_facets: Optional[List[str]],
    page: int,
    page_size: int,
) -> JobSearchBodyRequest:
    return JobSearchBodyRequest(
        queries=queries,
        locations=locations,
        sources=sources,
        skills=skills,
        companies=companies,
        industries=industries,
        work_models=work_models,
        employment_types=employment_types,
        experience_levels=experience_levels,
        salary_usd=salary_usd,
        posted_after=posted_after,
        include_facets=include_facets,
        page=page,
        page_size=page_size,
    )


class JobsSearchClient:
    """Synchronous sub-client for the Jobs Search endpoints.

    Access via ``client.search``.
    """

    def __init__(self, http: httpx.Client) -> None:
        self._client = http

    def search(
        self,
        *,
        q: Optional[str] = None,
        location: Optional[str] = None,
        sources: Optional[str] = None,
        work_model: Optional[str] = None,
        employment_type: Optional[str] = None,
        experience_level: Optional[str] = None,
        posted_after: Optional[datetime] = None,
        min_salary_usd: Optional[int] = None,
        max_salary_usd: Optional[int] = None,
        skills: Optional[str] = None,
        industries: Optional[str] = None,
        include_facets: Optional[str] = None,
        page: int = 1,
        page_size: int = 25,
    ) -> JobSearchResponse:
        """Search jobs using simple query parameters (GET /api/jobs).

        Args:
            q: Free-text search query.
            location: Location string filter.
            sources: Comma-separated source identifiers.
            work_model: Comma-separated work models ("remote", "hybrid", "onsite").
            employment_type: Comma-separated employment types.
            experience_level: Comma-separated experience levels.
            posted_after: Only jobs posted after this UTC datetime.
            min_salary_usd: Minimum salary (USD) filter.
            max_salary_usd: Maximum salary (USD) filter.
            skills: Comma-separated required skills.
            industries: Comma-separated company industries.
            include_facets: Comma-separated facets to compute. Pass ``""`` to skip
                facets entirely; omit (``None``) for the default subset.
            page: Page number (1-indexed).
            page_size: Results per page (1–100).

        Returns:
            A :class:`JobSearchResponse` with jobs and pagination metadata.
        """
        params = _simple_params(
            q=q,
            location=location,
            sources=sources,
            work_model=work_model,
            employment_type=employment_type,
            experience_level=experience_level,
            posted_after=posted_after,
            min_salary_usd=min_salary_usd,
            max_salary_usd=max_salary_usd,
            skills=skills,
            industries=industries,
            include_facets=include_facets,
            page=page,
            page_size=page_size,
        )
        resp = self._client.get("/api/jobs", params=params)
        if resp.status_code != 200:
            _handle_error(resp)
        return JobSearchResponse.model_validate(resp.json())

    def search_advanced(
        self,
        *,
        queries: Optional[List[str]] = None,
        locations: Optional[List[str]] = None,
        sources: Optional[List[str]] = None,
        skills: Optional[InclusionExclusionFilter] = None,
        companies: Optional[InclusionExclusionFilter] = None,
        industries: Optional[InclusionExclusionFilter] = None,
        work_models: Optional[List[str]] = None,
        employment_types: Optional[List[str]] = None,
        experience_levels: Optional[List[str]] = None,
        salary_usd: Optional[RangeFilter] = None,
        posted_after: Optional[datetime] = None,
        include_facets: Optional[List[str]] = None,
        page: int = 1,
        page_size: int = 25,
    ) -> JobSearchResponse:
        """Search jobs using the advanced body-based endpoint (POST /api/jobs/search).

        Args:
            queries: Multiple free-text search queries.
            locations: Multiple location strings.
            sources: ATS/source identifiers.
            skills: Include/exclude skills filter.
            companies: Include/exclude company-name filter.
            industries: Include/exclude company-industry filter.
            work_models: Work models ("remote", "hybrid", "onsite").
            employment_types: Employment types.
            experience_levels: Experience levels.
            salary_usd: Salary range (USD) filter.
            posted_after: Only jobs posted after this UTC datetime.
            include_facets: Facets to compute. Omit for the default subset; pass an
                empty list to skip facets entirely.
            page: Page number (1-indexed).
            page_size: Results per page (1–100).

        Returns:
            A :class:`JobSearchResponse` with jobs, pagination metadata, and facets.
        """
        request = _build_body(
            queries=queries,
            locations=locations,
            sources=sources,
            skills=skills,
            companies=companies,
            industries=industries,
            work_models=work_models,
            employment_types=employment_types,
            experience_levels=experience_levels,
            salary_usd=salary_usd,
            posted_after=posted_after,
            include_facets=include_facets,
            page=page,
            page_size=page_size,
        )
        resp = self._client.post("/api/jobs/search", json=request.model_dump(mode="json", exclude_none=True))
        if resp.status_code != 200:
            _handle_error(resp)
        return JobSearchResponse.model_validate(resp.json())

    def iter_jobs(
        self,
        *,
        queries: Optional[List[str]] = None,
        locations: Optional[List[str]] = None,
        sources: Optional[List[str]] = None,
        skills: Optional[InclusionExclusionFilter] = None,
        companies: Optional[InclusionExclusionFilter] = None,
        industries: Optional[InclusionExclusionFilter] = None,
        work_models: Optional[List[str]] = None,
        employment_types: Optional[List[str]] = None,
        experience_levels: Optional[List[str]] = None,
        salary_usd: Optional[RangeFilter] = None,
        posted_after: Optional[datetime] = None,
        page_size: int = 25,
    ) -> Iterator[Job]:
        """Iterate over all search results, automatically handling pagination.

        Uses the advanced search endpoint under the hood.

        Yields:
            Individual :class:`Job` objects.
        """
        page = 1
        while True:
            response = self.search_advanced(
                queries=queries,
                locations=locations,
                sources=sources,
                skills=skills,
                companies=companies,
                industries=industries,
                work_models=work_models,
                employment_types=employment_types,
                experience_levels=experience_levels,
                salary_usd=salary_usd,
                posted_after=posted_after,
                include_facets=[],
                page=page,
                page_size=page_size,
            )
            yield from response.jobs
            if page >= response.total_pages:
                break
            page += 1


class AsyncJobsSearchClient:
    """Asynchronous sub-client for the Jobs Search endpoints.

    Access via ``client.search``.
    """

    def __init__(self, http: httpx.AsyncClient) -> None:
        self._client = http

    async def search(
        self,
        *,
        q: Optional[str] = None,
        location: Optional[str] = None,
        sources: Optional[str] = None,
        work_model: Optional[str] = None,
        employment_type: Optional[str] = None,
        experience_level: Optional[str] = None,
        posted_after: Optional[datetime] = None,
        min_salary_usd: Optional[int] = None,
        max_salary_usd: Optional[int] = None,
        skills: Optional[str] = None,
        industries: Optional[str] = None,
        include_facets: Optional[str] = None,
        page: int = 1,
        page_size: int = 25,
    ) -> JobSearchResponse:
        """Search jobs using simple query parameters (GET /api/jobs)."""
        params = _simple_params(
            q=q,
            location=location,
            sources=sources,
            work_model=work_model,
            employment_type=employment_type,
            experience_level=experience_level,
            posted_after=posted_after,
            min_salary_usd=min_salary_usd,
            max_salary_usd=max_salary_usd,
            skills=skills,
            industries=industries,
            include_facets=include_facets,
            page=page,
            page_size=page_size,
        )
        resp = await self._client.get("/api/jobs", params=params)
        if resp.status_code != 200:
            _handle_error(resp)
        return JobSearchResponse.model_validate(resp.json())

    async def search_advanced(
        self,
        *,
        queries: Optional[List[str]] = None,
        locations: Optional[List[str]] = None,
        sources: Optional[List[str]] = None,
        skills: Optional[InclusionExclusionFilter] = None,
        companies: Optional[InclusionExclusionFilter] = None,
        industries: Optional[InclusionExclusionFilter] = None,
        work_models: Optional[List[str]] = None,
        employment_types: Optional[List[str]] = None,
        experience_levels: Optional[List[str]] = None,
        salary_usd: Optional[RangeFilter] = None,
        posted_after: Optional[datetime] = None,
        include_facets: Optional[List[str]] = None,
        page: int = 1,
        page_size: int = 25,
    ) -> JobSearchResponse:
        """Search jobs using the advanced body-based endpoint (POST /api/jobs/search)."""
        request = _build_body(
            queries=queries,
            locations=locations,
            sources=sources,
            skills=skills,
            companies=companies,
            industries=industries,
            work_models=work_models,
            employment_types=employment_types,
            experience_levels=experience_levels,
            salary_usd=salary_usd,
            posted_after=posted_after,
            include_facets=include_facets,
            page=page,
            page_size=page_size,
        )
        resp = await self._client.post("/api/jobs/search", json=request.model_dump(mode="json", exclude_none=True))
        if resp.status_code != 200:
            _handle_error(resp)
        return JobSearchResponse.model_validate(resp.json())

    async def iter_jobs(
        self,
        *,
        queries: Optional[List[str]] = None,
        locations: Optional[List[str]] = None,
        sources: Optional[List[str]] = None,
        skills: Optional[InclusionExclusionFilter] = None,
        companies: Optional[InclusionExclusionFilter] = None,
        industries: Optional[InclusionExclusionFilter] = None,
        work_models: Optional[List[str]] = None,
        employment_types: Optional[List[str]] = None,
        experience_levels: Optional[List[str]] = None,
        salary_usd: Optional[RangeFilter] = None,
        posted_after: Optional[datetime] = None,
        page_size: int = 25,
    ) -> AsyncIterator[Job]:
        """Iterate over all search results, automatically handling pagination."""
        page = 1
        while True:
            response = await self.search_advanced(
                queries=queries,
                locations=locations,
                sources=sources,
                skills=skills,
                companies=companies,
                industries=industries,
                work_models=work_models,
                employment_types=employment_types,
                experience_levels=experience_levels,
                salary_usd=salary_usd,
                posted_after=posted_after,
                include_facets=[],
                page=page,
                page_size=page_size,
            )
            for job in response.jobs:
                yield job
            if page >= response.total_pages:
                break
            page += 1
