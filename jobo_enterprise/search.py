"""Sub-client for the Jobs Search endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Any, AsyncIterator, Dict, Iterator, List, Optional, Union
from uuid import UUID

import httpx

from jobo_enterprise._transport import arequest, request
from jobo_enterprise.enums import EmploymentType, ExperienceLevel, WorkModel
from jobo_enterprise.models import (
    InclusionExclusionFilter,
    Job,
    JobSearchBodyRequest,
    JobSearchResponse,
    RangeFilter,
)

Enumish = Union[str, WorkModel, EmploymentType, ExperienceLevel]


def _simple_params(
    *,
    q: Optional[str],
    search_description: Optional[bool],
    location: Optional[str],
    sources: Optional[str],
    work_model: Optional[Enumish],
    employment_type: Optional[Enumish],
    experience_level: Optional[Enumish],
    posted_after: Optional[datetime],
    posted_before: Optional[datetime],
    discovered_after: Optional[datetime],
    discovered_before: Optional[datetime],
    min_salary_usd: Optional[int],
    max_salary_usd: Optional[int],
    skills: Optional[str],
    industries: Optional[str],
    include_facets: Optional[str],
    include_fields: Optional[str],
    page: int,
    page_size: int,
) -> Dict[str, Any]:
    params: Dict[str, Any] = {}
    if q:
        params["q"] = q
    if search_description is not None:
        params["search_description"] = str(search_description).lower()
    if location:
        params["location"] = location
    if sources:
        params["sources"] = sources
    if work_model:
        params["work_model"] = str(work_model)
    if employment_type:
        params["employment_type"] = str(employment_type)
    if experience_level:
        params["experience_level"] = str(experience_level)
    if posted_after:
        params["posted_after"] = posted_after.isoformat()
    if posted_before:
        params["posted_before"] = posted_before.isoformat()
    if discovered_after:
        params["discovered_after"] = discovered_after.isoformat()
    if discovered_before:
        params["discovered_before"] = discovered_before.isoformat()
    if min_salary_usd is not None:
        params["min_salary_usd"] = min_salary_usd
    if max_salary_usd is not None:
        params["max_salary_usd"] = max_salary_usd
    if skills:
        params["skills"] = skills
    if industries:
        params["industries"] = industries
    # Empty string is meaningful on both of these: it asks for no facets / core
    # fields only. Only None means "leave it out and take the default".
    if include_facets is not None:
        params["include_facets"] = include_facets
    if include_fields is not None:
        params["include_fields"] = include_fields
    params["page"] = page
    params["page_size"] = page_size
    return params


def _wire(values: Optional[List[Enumish]]) -> Optional[List[str]]:
    """Normalize enum members to their wire string so the body is plain str."""
    return [str(v) for v in values] if values is not None else None


def _build_body(
    *,
    queries: Optional[List[str]],
    search_description: Optional[bool],
    locations: Optional[List[str]],
    sources: Optional[List[str]],
    skills: Optional[InclusionExclusionFilter],
    companies: Optional[InclusionExclusionFilter],
    industries: Optional[InclusionExclusionFilter],
    work_models: Optional[List[Enumish]],
    employment_types: Optional[List[Enumish]],
    experience_levels: Optional[List[Enumish]],
    salary_usd: Optional[RangeFilter],
    posted_after: Optional[datetime],
    posted_before: Optional[datetime],
    discovered_after: Optional[datetime],
    discovered_before: Optional[datetime],
    include_facets: Optional[List[str]],
    include_fields: Optional[List[str]],
    page: int,
    page_size: int,
) -> JobSearchBodyRequest:
    return JobSearchBodyRequest(
        queries=queries,
        search_description=search_description,
        locations=locations,
        sources=sources,
        skills=skills,
        companies=companies,
        industries=industries,
        work_models=_wire(work_models),
        employment_types=_wire(employment_types),
        experience_levels=_wire(experience_levels),
        salary_usd=salary_usd,
        posted_after=posted_after,
        posted_before=posted_before,
        discovered_after=discovered_after,
        discovered_before=discovered_before,
        include_facets=include_facets,
        include_fields=include_fields,
        page=page,
        page_size=page_size,
    )


class JobsSearchClient:
    """Synchronous sub-client for the Jobs Search endpoints.

    Access via ``client.search``.
    """

    def __init__(self, http: httpx.Client) -> None:
        self._client = http

    def get_job(self, job_id: Union[UUID, str]) -> Job:
        """Fetch a single job by ID (GET /api/jobs/{id}).

        Unmetered — this endpoint deducts no wallet credits, though it still
        counts toward the per-key request rate limit. Raises
        :class:`~jobo_enterprise.exceptions.JoboNotFoundError` when no job has
        that ID.

        Args:
            job_id: The Jobo job UUID, as returned on every search and feed job.

        Returns:
            The :class:`Job`.
        """
        payload = request(self._client, "GET", f"/api/jobs/{job_id}")
        return Job.model_validate(payload)

    def search(
        self,
        *,
        q: Optional[str] = None,
        search_description: Optional[bool] = None,
        location: Optional[str] = None,
        sources: Optional[str] = None,
        work_model: Optional[Enumish] = None,
        employment_type: Optional[Enumish] = None,
        experience_level: Optional[Enumish] = None,
        posted_after: Optional[datetime] = None,
        posted_before: Optional[datetime] = None,
        discovered_after: Optional[datetime] = None,
        discovered_before: Optional[datetime] = None,
        min_salary_usd: Optional[int] = None,
        max_salary_usd: Optional[int] = None,
        skills: Optional[str] = None,
        industries: Optional[str] = None,
        include_facets: Optional[str] = None,
        include_fields: Optional[str] = None,
        page: int = 1,
        page_size: int = 25,
    ) -> JobSearchResponse:
        """Search jobs using simple query parameters (GET /api/jobs).

        Args:
            q: Free-text search query. Wrap it in double quotes for an exact,
                contiguous phrase match against the job title only.
            search_description: When ``True`` (the server default) match title,
                alternative titles, company, popular skills and summary. When
                ``False`` match titles and curated alternative titles only.
            location: Location string filter.
            sources: Comma-separated source identifiers.
            work_model: Work model filter. Accepts a :class:`WorkModel` member or
                its string value (``"remote"``, ``"hybrid"``, ``"onsite"``).
            employment_type: Employment type. Accepts an :class:`EmploymentType`
                member or its string value (``"full-time"``, ``"part-time"``, …).
            experience_level: Experience level. Accepts an :class:`ExperienceLevel`
                member or its string value.
            posted_after: Only jobs whose employer posting date is at or after this.
            posted_before: Only jobs whose employer posting date is at or before this.
            discovered_after: Only jobs first indexed at or after this UTC timestamp.
            discovered_before: Only jobs first indexed at or before this UTC timestamp.
            min_salary_usd: Minimum salary (USD) filter.
            max_salary_usd: Maximum salary (USD) filter.
            skills: Comma-separated required skills.
            industries: Comma-separated company industries.
            include_facets: Comma-separated facets to compute. Pass ``""`` to skip
                facets entirely; omit (``None``) for the default subset.
            include_fields: Comma-separated heavy fields to keep — ``description``,
                ``summary``, ``qualifications``, ``responsibilities``, ``benefits``.
                Omit (``None``) for the whole job; pass ``""`` for core fields only.
            page: Page number (1-indexed).
            page_size: Results per page (1–100).

        Returns:
            A :class:`JobSearchResponse` with jobs and pagination metadata.
        """
        params = _simple_params(
            q=q,
            search_description=search_description,
            location=location,
            sources=sources,
            work_model=work_model,
            employment_type=employment_type,
            experience_level=experience_level,
            posted_after=posted_after,
            posted_before=posted_before,
            discovered_after=discovered_after,
            discovered_before=discovered_before,
            min_salary_usd=min_salary_usd,
            max_salary_usd=max_salary_usd,
            skills=skills,
            industries=industries,
            include_facets=include_facets,
            include_fields=include_fields,
            page=page,
            page_size=page_size,
        )
        payload = request(self._client, "GET", "/api/jobs", params=params)
        return JobSearchResponse.model_validate(payload)

    def search_advanced(
        self,
        *,
        queries: Optional[List[str]] = None,
        search_description: Optional[bool] = None,
        locations: Optional[List[str]] = None,
        sources: Optional[List[str]] = None,
        skills: Optional[InclusionExclusionFilter] = None,
        companies: Optional[InclusionExclusionFilter] = None,
        industries: Optional[InclusionExclusionFilter] = None,
        work_models: Optional[List[Enumish]] = None,
        employment_types: Optional[List[Enumish]] = None,
        experience_levels: Optional[List[Enumish]] = None,
        salary_usd: Optional[RangeFilter] = None,
        posted_after: Optional[datetime] = None,
        posted_before: Optional[datetime] = None,
        discovered_after: Optional[datetime] = None,
        discovered_before: Optional[datetime] = None,
        include_facets: Optional[List[str]] = None,
        include_fields: Optional[List[str]] = None,
        page: int = 1,
        page_size: int = 25,
    ) -> JobSearchResponse:
        """Search jobs using the advanced body-based endpoint (POST /api/jobs/search).

        Args:
            queries: Multiple free-text search queries, OR'd. Prefix an entry with
                ``-`` to exclude it; maximum 10 positive terms.
            search_description: ``False`` restricts matching to titles and curated
                alternative titles. Defaults to ``True`` server-side.
            locations: Multiple location strings.
            sources: ATS/source identifiers.
            skills: Include/exclude skills filter.
            companies: Include/exclude company-name filter.
            industries: Include/exclude company-industry filter.
            work_models: Work models ("remote", "hybrid", "onsite").
            employment_types: Employment types ("full-time", "part-time", …).
            experience_levels: Experience levels ("intern", "entry", …).
            salary_usd: Salary range (USD) filter.
            posted_after: Only jobs whose employer posting date is at or after this.
            posted_before: Only jobs whose employer posting date is at or before this.
            discovered_after: Only jobs first indexed at or after this UTC timestamp.
            discovered_before: Only jobs first indexed at or before this UTC timestamp.
            include_facets: Facets to compute. Omit for the default subset; pass an
                empty list to skip facets entirely.
            include_fields: Heavy fields to keep. Omit for the whole job; pass an
                empty list for core fields only.
            page: Page number (1-indexed).
            page_size: Results per page (1–100).

        Returns:
            A :class:`JobSearchResponse` with jobs, pagination metadata, and facets.
        """
        body = _build_body(
            queries=queries,
            search_description=search_description,
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
            posted_before=posted_before,
            discovered_after=discovered_after,
            discovered_before=discovered_before,
            include_facets=include_facets,
            include_fields=include_fields,
            page=page,
            page_size=page_size,
        )
        payload = request(
            self._client,
            "POST",
            "/api/jobs/search",
            json=body.model_dump(mode="json", exclude_none=True),
        )
        return JobSearchResponse.model_validate(payload)

    def iter_jobs(
        self,
        *,
        queries: Optional[List[str]] = None,
        search_description: Optional[bool] = None,
        locations: Optional[List[str]] = None,
        sources: Optional[List[str]] = None,
        skills: Optional[InclusionExclusionFilter] = None,
        companies: Optional[InclusionExclusionFilter] = None,
        industries: Optional[InclusionExclusionFilter] = None,
        work_models: Optional[List[Enumish]] = None,
        employment_types: Optional[List[Enumish]] = None,
        experience_levels: Optional[List[Enumish]] = None,
        salary_usd: Optional[RangeFilter] = None,
        posted_after: Optional[datetime] = None,
        posted_before: Optional[datetime] = None,
        discovered_after: Optional[datetime] = None,
        discovered_before: Optional[datetime] = None,
        include_fields: Optional[List[str]] = None,
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
                search_description=search_description,
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
                posted_before=posted_before,
                discovered_after=discovered_after,
                discovered_before=discovered_before,
                include_facets=[],
                include_fields=include_fields,
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

    async def get_job(self, job_id: Union[UUID, str]) -> Job:
        """Fetch a single job by ID (GET /api/jobs/{id})."""
        payload = await arequest(self._client, "GET", f"/api/jobs/{job_id}")
        return Job.model_validate(payload)

    async def search(
        self,
        *,
        q: Optional[str] = None,
        search_description: Optional[bool] = None,
        location: Optional[str] = None,
        sources: Optional[str] = None,
        work_model: Optional[Enumish] = None,
        employment_type: Optional[Enumish] = None,
        experience_level: Optional[Enumish] = None,
        posted_after: Optional[datetime] = None,
        posted_before: Optional[datetime] = None,
        discovered_after: Optional[datetime] = None,
        discovered_before: Optional[datetime] = None,
        min_salary_usd: Optional[int] = None,
        max_salary_usd: Optional[int] = None,
        skills: Optional[str] = None,
        industries: Optional[str] = None,
        include_facets: Optional[str] = None,
        include_fields: Optional[str] = None,
        page: int = 1,
        page_size: int = 25,
    ) -> JobSearchResponse:
        """Search jobs using simple query parameters (GET /api/jobs)."""
        params = _simple_params(
            q=q,
            search_description=search_description,
            location=location,
            sources=sources,
            work_model=work_model,
            employment_type=employment_type,
            experience_level=experience_level,
            posted_after=posted_after,
            posted_before=posted_before,
            discovered_after=discovered_after,
            discovered_before=discovered_before,
            min_salary_usd=min_salary_usd,
            max_salary_usd=max_salary_usd,
            skills=skills,
            industries=industries,
            include_facets=include_facets,
            include_fields=include_fields,
            page=page,
            page_size=page_size,
        )
        payload = await arequest(self._client, "GET", "/api/jobs", params=params)
        return JobSearchResponse.model_validate(payload)

    async def search_advanced(
        self,
        *,
        queries: Optional[List[str]] = None,
        search_description: Optional[bool] = None,
        locations: Optional[List[str]] = None,
        sources: Optional[List[str]] = None,
        skills: Optional[InclusionExclusionFilter] = None,
        companies: Optional[InclusionExclusionFilter] = None,
        industries: Optional[InclusionExclusionFilter] = None,
        work_models: Optional[List[Enumish]] = None,
        employment_types: Optional[List[Enumish]] = None,
        experience_levels: Optional[List[Enumish]] = None,
        salary_usd: Optional[RangeFilter] = None,
        posted_after: Optional[datetime] = None,
        posted_before: Optional[datetime] = None,
        discovered_after: Optional[datetime] = None,
        discovered_before: Optional[datetime] = None,
        include_facets: Optional[List[str]] = None,
        include_fields: Optional[List[str]] = None,
        page: int = 1,
        page_size: int = 25,
    ) -> JobSearchResponse:
        """Search jobs using the advanced body-based endpoint (POST /api/jobs/search)."""
        body = _build_body(
            queries=queries,
            search_description=search_description,
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
            posted_before=posted_before,
            discovered_after=discovered_after,
            discovered_before=discovered_before,
            include_facets=include_facets,
            include_fields=include_fields,
            page=page,
            page_size=page_size,
        )
        payload = await arequest(
            self._client,
            "POST",
            "/api/jobs/search",
            json=body.model_dump(mode="json", exclude_none=True),
        )
        return JobSearchResponse.model_validate(payload)

    async def iter_jobs(
        self,
        *,
        queries: Optional[List[str]] = None,
        search_description: Optional[bool] = None,
        locations: Optional[List[str]] = None,
        sources: Optional[List[str]] = None,
        skills: Optional[InclusionExclusionFilter] = None,
        companies: Optional[InclusionExclusionFilter] = None,
        industries: Optional[InclusionExclusionFilter] = None,
        work_models: Optional[List[Enumish]] = None,
        employment_types: Optional[List[Enumish]] = None,
        experience_levels: Optional[List[Enumish]] = None,
        salary_usd: Optional[RangeFilter] = None,
        posted_after: Optional[datetime] = None,
        posted_before: Optional[datetime] = None,
        discovered_after: Optional[datetime] = None,
        discovered_before: Optional[datetime] = None,
        include_fields: Optional[List[str]] = None,
        page_size: int = 25,
    ) -> AsyncIterator[Job]:
        """Iterate over all search results, automatically handling pagination."""
        page = 1
        while True:
            response = await self.search_advanced(
                queries=queries,
                search_description=search_description,
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
                posted_before=posted_before,
                discovered_after=discovered_after,
                discovered_before=discovered_before,
                include_facets=[],
                include_fields=include_fields,
                page=page,
                page_size=page_size,
            )
            for job in response.jobs:
                yield job
            if page >= response.total_pages:
                break
            page += 1
