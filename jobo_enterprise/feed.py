"""Sub-client for the Jobs Feed endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Any, AsyncIterator, Dict, Iterator, List, Optional, Union
from uuid import UUID

import httpx

from jobo_enterprise._transport import DEFAULT_FEED_TIMEOUT, arequest, request
from jobo_enterprise.enums import EmploymentType, ExperienceLevel, WorkModel
from jobo_enterprise.models import (
    Job,
    JobFeedRequest,
    JobFeedResponse,
    ExpiredJobIdsResponse,
    LocationFilter,
    ManagedJobFeedRequest,
)

_FEED_PATH = "/api/jobs/feed"
_MANAGED_FEED_PATH = "/api/jobs/feed/managed"

Enumish = Union[str, WorkModel, EmploymentType, ExperienceLevel]


def _wire(values: Optional[List[Enumish]]) -> Optional[List[str]]:
    """Normalize enum members to their wire string so the body is plain str."""
    return [str(v) for v in values] if values is not None else None


def _feed_body(
    *,
    locations: Optional[List[LocationFilter]],
    sources: Optional[List[str]],
    work_models: Optional[List[Enumish]],
    employment_types: Optional[List[Enumish]],
    experience_levels: Optional[List[Enumish]],
    posted_after: Optional[datetime],
    updated_after: Optional[datetime],
    stable_scan: Optional[bool],
    batch_size: int,
) -> Dict[str, Any]:
    request_model = JobFeedRequest(
        locations=locations,
        sources=sources,
        work_models=_wire(work_models),
        employment_types=_wire(employment_types),
        experience_levels=_wire(experience_levels),
        posted_after=posted_after,
        updated_after=updated_after,
        stable_scan=stable_scan,
        batch_size=batch_size,
    )
    return request_model.model_dump(mode="json", exclude_none=True)


def _managed_feed_body(
    *,
    sources: Optional[List[str]],
    work_models: Optional[List[Enumish]],
    posted_after: Optional[datetime],
    updated_after: Optional[datetime],
    batch_size: int,
) -> Dict[str, Any]:
    request_model = ManagedJobFeedRequest(
        sources=sources,
        work_models=_wire(work_models),
        posted_after=posted_after,
        updated_after=updated_after,
        batch_size=batch_size,
    )
    return request_model.model_dump(mode="json", exclude_none=True)


def _expired_params(
    expired_since: Optional[datetime], cursor: Optional[str], batch_size: int
) -> Dict[str, Union[str, int]]:
    params: Dict[str, Union[str, int]] = {"batch_size": batch_size}
    if expired_since is not None:
        params["expired_since"] = expired_since.isoformat()
    if cursor:
        params["cursor"] = cursor
    return params


class JobsFeedClient:
    """Synchronous sub-client for the Jobs Feed endpoints.

    Access via ``client.feed``.
    """

    def __init__(self, http: httpx.Client, feed_timeout: float = DEFAULT_FEED_TIMEOUT) -> None:
        self._client = http
        self._feed_timeout = feed_timeout

    def get_jobs(
        self,
        *,
        locations: Optional[List[LocationFilter]] = None,
        sources: Optional[List[str]] = None,
        work_models: Optional[List[Enumish]] = None,
        employment_types: Optional[List[Enumish]] = None,
        experience_levels: Optional[List[Enumish]] = None,
        posted_after: Optional[datetime] = None,
        updated_after: Optional[datetime] = None,
        stable_scan: Optional[bool] = None,
        cursor: Optional[str] = None,
        batch_size: int = 1000,
    ) -> JobFeedResponse:
        """Fetch a single batch of jobs from the feed.

        Args:
            locations: Structured location filters. Job matches ANY provided location.
            sources: ATS/source identifiers (e.g. ``"greenhouse"``, ``"workday"``).
            work_models: Work models to include, e.g. ``["remote", "hybrid"]``. ``None`` = all.
            employment_types: Employment types to include, e.g. ``["full-time"]``. ``None`` = all.
            experience_levels: Experience levels to include, e.g. ``["senior"]``. ``None`` = all.
            posted_after: Only jobs whose posting or first-indexed time is at or after this.
            updated_after: Only jobs created or updated at or after this — the
                incremental-sync watermark.
            stable_scan: Page by immutable creation time. Defaults to ``True``
                server-side; pass ``False`` for the legacy update-recency ordering.
            cursor: Pagination cursor from a previous response. When supplied it is
                sent on its own — the cursor already carries the filters and batch
                size from the first request, and anything sent beside it is ignored.
            batch_size: Number of jobs per batch (1–1000). Defaults to 1000.

        Returns:
            A :class:`JobFeedResponse` with jobs, cursor, and pagination flag.
        """
        body = (
            {"cursor": cursor}
            if cursor
            else _feed_body(
                locations=locations,
                sources=sources,
                work_models=work_models,
                employment_types=employment_types,
                experience_levels=experience_levels,
                posted_after=posted_after,
                updated_after=updated_after,
                stable_scan=stable_scan,
                batch_size=batch_size,
            )
        )
        payload = request(
            self._client, "POST", _FEED_PATH, json=body, timeout=self._feed_timeout
        )
        return JobFeedResponse.model_validate(payload)

    def iter_jobs(
        self,
        *,
        locations: Optional[List[LocationFilter]] = None,
        sources: Optional[List[str]] = None,
        work_models: Optional[List[Enumish]] = None,
        employment_types: Optional[List[Enumish]] = None,
        experience_levels: Optional[List[Enumish]] = None,
        posted_after: Optional[datetime] = None,
        updated_after: Optional[datetime] = None,
        stable_scan: Optional[bool] = None,
        batch_size: int = 1000,
    ) -> Iterator[Job]:
        """Iterate over all jobs in the feed, automatically handling pagination.

        Yields:
            Individual :class:`Job` objects.
        """
        response = self.get_jobs(
            locations=locations,
            sources=sources,
            work_models=work_models,
            employment_types=employment_types,
            experience_levels=experience_levels,
            posted_after=posted_after,
            updated_after=updated_after,
            stable_scan=stable_scan,
            batch_size=batch_size,
        )
        while True:
            yield from response.jobs
            if not response.has_more or not response.next_cursor:
                break
            response = self.get_jobs(cursor=response.next_cursor)

    def get_managed_jobs(
        self,
        *,
        sources: Optional[List[str]] = None,
        work_models: Optional[List[Enumish]] = None,
        posted_after: Optional[datetime] = None,
        updated_after: Optional[datetime] = None,
        cursor: Optional[str] = None,
        batch_size: int = 1000,
    ) -> JobFeedResponse:
        """Fetch a single batch from the managed feed (POST /api/jobs/feed/managed).

        Returns only jobs from companies configured through Managed Job Scraping
        in the Jobo portal. Same batch and cursor semantics as :meth:`get_jobs`,
        with no ``locations`` filter. Raises
        :class:`~jobo_enterprise.exceptions.JoboPermissionError` for sandbox and
        marketplace keys, which carry no managed job sources.
        """
        body = (
            {"cursor": cursor}
            if cursor
            else _managed_feed_body(
                sources=sources,
                work_models=work_models,
                posted_after=posted_after,
                updated_after=updated_after,
                batch_size=batch_size,
            )
        )
        payload = request(
            self._client, "POST", _MANAGED_FEED_PATH, json=body, timeout=self._feed_timeout
        )
        return JobFeedResponse.model_validate(payload)

    def iter_managed_jobs(
        self,
        *,
        sources: Optional[List[str]] = None,
        work_models: Optional[List[Enumish]] = None,
        posted_after: Optional[datetime] = None,
        updated_after: Optional[datetime] = None,
        batch_size: int = 1000,
    ) -> Iterator[Job]:
        """Iterate over the whole managed feed, handling pagination."""
        response = self.get_managed_jobs(
            sources=sources,
            work_models=work_models,
            posted_after=posted_after,
            updated_after=updated_after,
            batch_size=batch_size,
        )
        while True:
            yield from response.jobs
            if not response.has_more or not response.next_cursor:
                break
            response = self.get_managed_jobs(cursor=response.next_cursor)

    def get_expired_job_ids(
        self,
        *,
        expired_since: Optional[datetime] = None,
        cursor: Optional[str] = None,
        batch_size: int = 1000,
    ) -> ExpiredJobIdsResponse:
        """Fetch a single batch of expired job IDs.

        Args:
            expired_since: UTC timestamp. Optional — defaults to 24 hours ago
                server-side. Maximum lookback is 7 days.
            cursor: Pagination cursor from a previous response.
            batch_size: Number of IDs per batch (1–10000). Defaults to 1000.

        Returns:
            An :class:`ExpiredJobIdsResponse` with job IDs and pagination info.
        """
        payload = request(
            self._client,
            "GET",
            "/api/jobs/expired",
            params=_expired_params(expired_since, cursor, batch_size),
        )
        return ExpiredJobIdsResponse.model_validate(payload)

    def iter_expired_job_ids(
        self,
        *,
        expired_since: Optional[datetime] = None,
        batch_size: int = 1000,
    ) -> Iterator[UUID]:
        """Iterate over all expired job IDs, automatically handling pagination.

        Yields:
            Individual job UUIDs.
        """
        cursor: Optional[str] = None
        while True:
            response = self.get_expired_job_ids(
                expired_since=expired_since,
                cursor=cursor,
                batch_size=batch_size,
            )
            yield from response.job_ids
            if not response.has_more or not response.next_cursor:
                break
            cursor = response.next_cursor


class AsyncJobsFeedClient:
    """Asynchronous sub-client for the Jobs Feed endpoints.

    Access via ``client.feed``.
    """

    def __init__(
        self, http: httpx.AsyncClient, feed_timeout: float = DEFAULT_FEED_TIMEOUT
    ) -> None:
        self._client = http
        self._feed_timeout = feed_timeout

    async def get_jobs(
        self,
        *,
        locations: Optional[List[LocationFilter]] = None,
        sources: Optional[List[str]] = None,
        work_models: Optional[List[Enumish]] = None,
        employment_types: Optional[List[Enumish]] = None,
        experience_levels: Optional[List[Enumish]] = None,
        posted_after: Optional[datetime] = None,
        updated_after: Optional[datetime] = None,
        stable_scan: Optional[bool] = None,
        cursor: Optional[str] = None,
        batch_size: int = 1000,
    ) -> JobFeedResponse:
        """Fetch a single batch of jobs from the feed."""
        body = (
            {"cursor": cursor}
            if cursor
            else _feed_body(
                locations=locations,
                sources=sources,
                work_models=work_models,
                employment_types=employment_types,
                experience_levels=experience_levels,
                posted_after=posted_after,
                updated_after=updated_after,
                stable_scan=stable_scan,
                batch_size=batch_size,
            )
        )
        payload = await arequest(
            self._client, "POST", _FEED_PATH, json=body, timeout=self._feed_timeout
        )
        return JobFeedResponse.model_validate(payload)

    async def iter_jobs(
        self,
        *,
        locations: Optional[List[LocationFilter]] = None,
        sources: Optional[List[str]] = None,
        work_models: Optional[List[Enumish]] = None,
        employment_types: Optional[List[Enumish]] = None,
        experience_levels: Optional[List[Enumish]] = None,
        posted_after: Optional[datetime] = None,
        updated_after: Optional[datetime] = None,
        stable_scan: Optional[bool] = None,
        batch_size: int = 1000,
    ) -> AsyncIterator[Job]:
        """Iterate over all jobs in the feed, automatically handling pagination."""
        response = await self.get_jobs(
            locations=locations,
            sources=sources,
            work_models=work_models,
            employment_types=employment_types,
            experience_levels=experience_levels,
            posted_after=posted_after,
            updated_after=updated_after,
            stable_scan=stable_scan,
            batch_size=batch_size,
        )
        while True:
            for job in response.jobs:
                yield job
            if not response.has_more or not response.next_cursor:
                break
            response = await self.get_jobs(cursor=response.next_cursor)

    async def get_managed_jobs(
        self,
        *,
        sources: Optional[List[str]] = None,
        work_models: Optional[List[Enumish]] = None,
        posted_after: Optional[datetime] = None,
        updated_after: Optional[datetime] = None,
        cursor: Optional[str] = None,
        batch_size: int = 1000,
    ) -> JobFeedResponse:
        """Fetch a single batch from the managed feed."""
        body = (
            {"cursor": cursor}
            if cursor
            else _managed_feed_body(
                sources=sources,
                work_models=work_models,
                posted_after=posted_after,
                updated_after=updated_after,
                batch_size=batch_size,
            )
        )
        payload = await arequest(
            self._client, "POST", _MANAGED_FEED_PATH, json=body, timeout=self._feed_timeout
        )
        return JobFeedResponse.model_validate(payload)

    async def iter_managed_jobs(
        self,
        *,
        sources: Optional[List[str]] = None,
        work_models: Optional[List[Enumish]] = None,
        posted_after: Optional[datetime] = None,
        updated_after: Optional[datetime] = None,
        batch_size: int = 1000,
    ) -> AsyncIterator[Job]:
        """Iterate over the whole managed feed, handling pagination."""
        response = await self.get_managed_jobs(
            sources=sources,
            work_models=work_models,
            posted_after=posted_after,
            updated_after=updated_after,
            batch_size=batch_size,
        )
        while True:
            for job in response.jobs:
                yield job
            if not response.has_more or not response.next_cursor:
                break
            response = await self.get_managed_jobs(cursor=response.next_cursor)

    async def get_expired_job_ids(
        self,
        *,
        expired_since: Optional[datetime] = None,
        cursor: Optional[str] = None,
        batch_size: int = 1000,
    ) -> ExpiredJobIdsResponse:
        """Fetch a single batch of expired job IDs."""
        payload = await arequest(
            self._client,
            "GET",
            "/api/jobs/expired",
            params=_expired_params(expired_since, cursor, batch_size),
        )
        return ExpiredJobIdsResponse.model_validate(payload)

    async def iter_expired_job_ids(
        self,
        *,
        expired_since: Optional[datetime] = None,
        batch_size: int = 1000,
    ) -> AsyncIterator[UUID]:
        """Iterate over all expired job IDs, automatically handling pagination."""
        cursor: Optional[str] = None
        while True:
            response = await self.get_expired_job_ids(
                expired_since=expired_since,
                cursor=cursor,
                batch_size=batch_size,
            )
            for job_id in response.job_ids:
                yield job_id
            if not response.has_more or not response.next_cursor:
                break
            cursor = response.next_cursor
