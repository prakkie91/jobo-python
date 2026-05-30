"""Sub-client for the Jobs Feed endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import AsyncIterator, Iterator, List, Optional, Union
from uuid import UUID

import httpx

from jobo_enterprise.enums import WorkModel
from jobo_enterprise.exceptions import _handle_error
from jobo_enterprise.models import (
    Job,
    JobFeedRequest,
    JobFeedResponse,
    ExpiredJobIdsResponse,
    LocationFilter,
)


class JobsFeedClient:
    """Synchronous sub-client for the Jobs Feed endpoints.

    Access via ``client.feed``.
    """

    def __init__(self, http: httpx.Client) -> None:
        self._client = http

    def get_jobs(
        self,
        *,
        locations: Optional[List[LocationFilter]] = None,
        sources: Optional[List[str]] = None,
        work_models: Optional[List[Union[str, WorkModel]]] = None,
        posted_after: Optional[datetime] = None,
        cursor: Optional[str] = None,
        batch_size: int = 1000,
    ) -> JobFeedResponse:
        """Fetch a single batch of jobs from the feed.

        Args:
            locations: Structured location filters. Job matches ANY provided location.
            sources: ATS/source identifiers (e.g. ``"greenhouse"``, ``"workday"``).
            work_models: Work models to include, e.g. ``["remote", "hybrid"]``. ``None`` = all.
            posted_after: Only jobs posted after this UTC datetime.
            cursor: Pagination cursor from a previous response.
            batch_size: Number of jobs per batch (1–1000). Defaults to 1000.

        Returns:
            A :class:`JobFeedResponse` with jobs, cursor, and pagination flag.
        """
        request = JobFeedRequest(
            locations=locations,
            sources=sources,
            # Normalize enum members to their wire string so the body is plain str.
            work_models=[str(v) for v in work_models] if work_models is not None else None,
            posted_after=posted_after,
            cursor=cursor,
            batch_size=batch_size,
        )
        resp = self._client.post("/api/jobs/feed", json=request.model_dump(mode="json", exclude_none=True))
        if resp.status_code != 200:
            _handle_error(resp)
        return JobFeedResponse.model_validate(resp.json())

    def iter_jobs(
        self,
        *,
        locations: Optional[List[LocationFilter]] = None,
        sources: Optional[List[str]] = None,
        work_models: Optional[List[Union[str, WorkModel]]] = None,
        posted_after: Optional[datetime] = None,
        batch_size: int = 1000,
    ) -> Iterator[Job]:
        """Iterate over all jobs in the feed, automatically handling pagination.

        Yields:
            Individual :class:`Job` objects.
        """
        cursor: Optional[str] = None
        while True:
            response = self.get_jobs(
                locations=locations,
                sources=sources,
                work_models=work_models,
                posted_after=posted_after,
                cursor=cursor,
                batch_size=batch_size,
            )
            yield from response.jobs
            if not response.has_more:
                break
            cursor = response.next_cursor

    def get_expired_job_ids(
        self,
        *,
        expired_since: datetime,
        cursor: Optional[str] = None,
        batch_size: int = 1000,
    ) -> ExpiredJobIdsResponse:
        """Fetch a single batch of expired job IDs.

        Args:
            expired_since: UTC timestamp. Max 7 days in the past.
            cursor: Pagination cursor from a previous response.
            batch_size: Number of IDs per batch (1–10000). Defaults to 1000.

        Returns:
            An :class:`ExpiredJobIdsResponse` with job IDs and pagination info.
        """
        params: dict[str, Union[str, int]] = {
            "expired_since": expired_since.isoformat(),
            "batch_size": batch_size,
        }
        if cursor:
            params["cursor"] = cursor
        resp = self._client.get("/api/jobs/expired", params=params)
        if resp.status_code != 200:
            _handle_error(resp)
        return ExpiredJobIdsResponse.model_validate(resp.json())

    def iter_expired_job_ids(
        self,
        *,
        expired_since: datetime,
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
            if not response.has_more:
                break
            cursor = response.next_cursor


class AsyncJobsFeedClient:
    """Asynchronous sub-client for the Jobs Feed endpoints.

    Access via ``client.feed``.
    """

    def __init__(self, http: httpx.AsyncClient) -> None:
        self._client = http

    async def get_jobs(
        self,
        *,
        locations: Optional[List[LocationFilter]] = None,
        sources: Optional[List[str]] = None,
        work_models: Optional[List[Union[str, WorkModel]]] = None,
        posted_after: Optional[datetime] = None,
        cursor: Optional[str] = None,
        batch_size: int = 1000,
    ) -> JobFeedResponse:
        """Fetch a single batch of jobs from the feed."""
        request = JobFeedRequest(
            locations=locations,
            sources=sources,
            # Normalize enum members to their wire string so the body is plain str.
            work_models=[str(v) for v in work_models] if work_models is not None else None,
            posted_after=posted_after,
            cursor=cursor,
            batch_size=batch_size,
        )
        resp = await self._client.post("/api/jobs/feed", json=request.model_dump(mode="json", exclude_none=True))
        if resp.status_code != 200:
            _handle_error(resp)
        return JobFeedResponse.model_validate(resp.json())

    async def iter_jobs(
        self,
        *,
        locations: Optional[List[LocationFilter]] = None,
        sources: Optional[List[str]] = None,
        work_models: Optional[List[Union[str, WorkModel]]] = None,
        posted_after: Optional[datetime] = None,
        batch_size: int = 1000,
    ) -> AsyncIterator[Job]:
        """Iterate over all jobs in the feed, automatically handling pagination."""
        cursor: Optional[str] = None
        while True:
            response = await self.get_jobs(
                locations=locations,
                sources=sources,
                work_models=work_models,
                posted_after=posted_after,
                cursor=cursor,
                batch_size=batch_size,
            )
            for job in response.jobs:
                yield job
            if not response.has_more:
                break
            cursor = response.next_cursor

    async def get_expired_job_ids(
        self,
        *,
        expired_since: datetime,
        cursor: Optional[str] = None,
        batch_size: int = 1000,
    ) -> ExpiredJobIdsResponse:
        """Fetch a single batch of expired job IDs."""
        params: dict[str, Union[str, int]] = {
            "expired_since": expired_since.isoformat(),
            "batch_size": batch_size,
        }
        if cursor:
            params["cursor"] = cursor
        resp = await self._client.get("/api/jobs/expired", params=params)
        if resp.status_code != 200:
            _handle_error(resp)
        return ExpiredJobIdsResponse.model_validate(resp.json())

    async def iter_expired_job_ids(
        self,
        *,
        expired_since: datetime,
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
            if not response.has_more:
                break
            cursor = response.next_cursor
